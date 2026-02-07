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
