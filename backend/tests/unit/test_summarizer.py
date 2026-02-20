from unittest.mock import MagicMock, patch

import pytest

from app.services.summarizer import generate_summary


class TestGenerateSummary:
    """Test generate_summary() with mocked OpenAI client."""

    @pytest.fixture
    def mock_openai_response(self) -> MagicMock:
        """Create a mock OpenAI chat completion response."""
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = "This is a summary of the video."
        return response

    @patch("app.services.summarizer.OpenAI")
    def test_returns_summary_text(
        self, mock_openai_class: MagicMock, mock_openai_response: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response

        result = generate_summary("This is a transcript about Python programming.")

        assert result == "This is a summary of the video."

    @patch("app.services.summarizer.OpenAI")
    def test_uses_gpt4o_mini_model(
        self, mock_openai_class: MagicMock, mock_openai_response: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response

        generate_summary("Some transcript text.")

        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["model"] == "gpt-4o-mini"

    @patch("app.services.summarizer.OpenAI")
    def test_includes_system_prompt(
        self, mock_openai_class: MagicMock, mock_openai_response: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response

        generate_summary("Some transcript text.")

        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs["messages"]
        system_msg = next(m for m in messages if m["role"] == "system")
        content = system_msg["content"].lower()
        assert "summary" in content or "summarize" in content

    @patch("app.services.summarizer.OpenAI")
    def test_passes_transcript_as_user_message(
        self, mock_openai_class: MagicMock, mock_openai_response: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response

        transcript = "Hello, this is a test transcript about coding."
        generate_summary(transcript)

        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs["messages"]
        user_message = next(m for m in messages if m["role"] == "user")
        assert transcript in user_message["content"]

    @patch("app.services.summarizer.OpenAI")
    def test_sets_timeout(
        self, mock_openai_class: MagicMock, mock_openai_response: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response

        generate_summary("Some text.")

        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs.get("timeout") == 30

    @patch("app.services.summarizer.OpenAI")
    def test_chunked_summarization_for_long_transcript(
        self, mock_openai_class: MagicMock
    ) -> None:
        """Test that very long transcripts are chunked and individually summarized."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # First calls return chunk summaries, last call returns final summary
        chunk_response_1 = MagicMock()
        chunk_response_1.choices = [MagicMock()]
        chunk_response_1.choices[0].message.content = "Summary of chunk 1."

        chunk_response_2 = MagicMock()
        chunk_response_2.choices = [MagicMock()]
        chunk_response_2.choices[0].message.content = "Summary of chunk 2."

        final_response = MagicMock()
        final_response.choices = [MagicMock()]
        final_response.choices[0].message.content = "Combined final summary."

        mock_client.chat.completions.create.side_effect = [
            chunk_response_1,
            chunk_response_2,
            final_response,
        ]

        # Create a transcript that exceeds the token limit (~100K tokens ≈ 400K chars)
        long_transcript = "word " * 120_000  # ~600K chars, well over 100K tokens

        result = generate_summary(long_transcript)

        assert result == "Combined final summary."
        # Should have been called multiple times (chunks + final)
        assert mock_client.chat.completions.create.call_count >= 3


class TestGenerateSummaryWithLength:
    """Test generate_summary() with length_percent and transcript_word_count."""

    @pytest.fixture
    def mock_openai_response(self) -> MagicMock:
        """Create a mock OpenAI chat completion response."""
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = "A length-guided summary."
        return response

    @patch("app.services.summarizer.OpenAI")
    def test_includes_target_word_count_in_prompt(
        self, mock_openai_class: MagicMock, mock_openai_response: MagicMock
    ) -> None:
        """When transcript_word_count and length_percent are provided,
        the system prompt should include the target word count."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response

        # 1000 words * 20% = 200 target words
        generate_summary(
            "word " * 1000,
            transcript_word_count=1000,
            length_percent=20,
        )

        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs["messages"]
        system_msg = next(m for m in messages if m["role"] == "system")
        assert "200" in system_msg["content"]
        assert "20%" in system_msg["content"]

    @patch("app.services.summarizer.OpenAI")
    def test_default_behavior_no_length_params(
        self, mock_openai_class: MagicMock, mock_openai_response: MagicMock
    ) -> None:
        """Without length params, the system prompt should be the original
        (no word count target)."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response

        generate_summary("Some transcript text.")

        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs["messages"]
        system_msg = next(m for m in messages if m["role"] == "system")
        # Should not contain any word count target
        assert "approximately" not in system_msg["content"]
        assert "words" not in system_msg["content"].lower().split("key")[0]

    @patch("app.services.summarizer.OpenAI")
    def test_target_calculation_at_50_percent(
        self, mock_openai_class: MagicMock, mock_openai_response: MagicMock
    ) -> None:
        """50% of 500 words = 250 target words."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response

        generate_summary(
            "word " * 500,
            transcript_word_count=500,
            length_percent=50,
        )

        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs["messages"]
        system_msg = next(m for m in messages if m["role"] == "system")
        assert "250" in system_msg["content"]

    @patch("app.services.summarizer.OpenAI")
    def test_target_calculation_at_10_percent(
        self, mock_openai_class: MagicMock, mock_openai_response: MagicMock
    ) -> None:
        """10% of 2000 words = 200 target words."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response

        generate_summary(
            "word " * 2000,
            transcript_word_count=2000,
            length_percent=10,
        )

        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs["messages"]
        system_msg = next(m for m in messages if m["role"] == "system")
        assert "200" in system_msg["content"]

    @patch("app.services.summarizer.OpenAI")
    def test_chunked_summarization_includes_target_in_combine(
        self, mock_openai_class: MagicMock
    ) -> None:
        """For chunked transcripts, the combine step should include the
        overall target word count."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        chunk_response_1 = MagicMock()
        chunk_response_1.choices = [MagicMock()]
        chunk_response_1.choices[0].message.content = "Summary of chunk 1."

        chunk_response_2 = MagicMock()
        chunk_response_2.choices = [MagicMock()]
        chunk_response_2.choices[0].message.content = "Summary of chunk 2."

        final_response = MagicMock()
        final_response.choices = [MagicMock()]
        final_response.choices[0].message.content = "Combined final summary."

        mock_client.chat.completions.create.side_effect = [
            chunk_response_1,
            chunk_response_2,
            final_response,
        ]

        # Create a transcript that exceeds the token limit
        long_transcript = "word " * 120_000

        generate_summary(
            long_transcript,
            transcript_word_count=120_000,
            length_percent=25,
        )

        # The last call (combine step) should include target word count
        last_call = mock_client.chat.completions.create.call_args_list[-1]
        messages = last_call.kwargs["messages"]
        system_msg = next(m for m in messages if m["role"] == "system")
        # 25% of 120,000 = 30,000
        assert "30000" in system_msg["content"]
