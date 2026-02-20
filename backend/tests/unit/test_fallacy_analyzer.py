import json
from unittest.mock import MagicMock, patch

from app.services.fallacy_analyzer import analyze_fallacies


def _make_valid_response_json() -> str:
    """Return a valid JSON string matching FallacyAnalysisResult schema."""
    return json.dumps(
        {
            "summary": {
                "total_fallacies": 1,
                "high_severity": 1,
                "medium_severity": 0,
                "low_severity": 0,
                "primary_tactics": ["Ad Hominem"],
            },
            "fallacies": [
                {
                    "timestamp": None,
                    "quote": "You can't trust him",
                    "fallacy_name": "Ad Hominem",
                    "category": "Relevance",
                    "severity": "high",
                    "explanation": "Attacks the person rather than the argument.",
                    "clear_example": {
                        "scenario": "Dismissing a mechanic",
                        "why_wrong": "Expertise comes from experience",
                    },
                }
            ],
        }
    )


class TestAnalyzeFallacies:
    @patch("app.services.fallacy_analyzer.OpenAI")
    def test_returns_fallacy_analysis_result(
        self, mock_openai_class: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = _make_valid_response_json()
        mock_client.chat.completions.create.return_value = mock_response

        result = analyze_fallacies("Some transcript text.")

        assert result is not None
        assert result.summary.total_fallacies == 1
        assert len(result.fallacies) == 1
        assert result.fallacies[0].fallacy_name == "Ad Hominem"

    @patch("app.services.fallacy_analyzer.OpenAI")
    def test_system_prompt_contains_fallacy_instructions(
        self, mock_openai_class: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = _make_valid_response_json()
        mock_client.chat.completions.create.return_value = mock_response

        analyze_fallacies("Some text.")

        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs["messages"]
        system_msg = next(m for m in messages if m["role"] == "system")
        assert "fallac" in system_msg["content"].lower()

    @patch("app.services.fallacy_analyzer.OpenAI")
    def test_transcript_passed_as_user_message(
        self, mock_openai_class: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = _make_valid_response_json()
        mock_client.chat.completions.create.return_value = mock_response

        analyze_fallacies("My specific transcript content.")

        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs["messages"]
        user_msg = next(m for m in messages if m["role"] == "user")
        assert "My specific transcript content." in user_msg["content"]

    @patch("app.services.fallacy_analyzer.OpenAI")
    def test_uses_json_mode(self, mock_openai_class: MagicMock) -> None:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = _make_valid_response_json()
        mock_client.chat.completions.create.return_value = mock_response

        analyze_fallacies("Some text.")

        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["response_format"] == {"type": "json_object"}

    @patch("app.services.fallacy_analyzer.OpenAI")
    def test_returns_none_on_malformed_json(self, mock_openai_class: MagicMock) -> None:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"bad": "data"}'
        mock_client.chat.completions.create.return_value = mock_response

        result = analyze_fallacies("Some text.")

        assert result is None

    @patch("app.services.fallacy_analyzer.OpenAI")
    def test_returns_none_on_api_error(self, mock_openai_class: MagicMock) -> None:
        from openai import APIError

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = APIError(
            message="Rate limit exceeded",
            request=MagicMock(),
            body=None,
        )

        result = analyze_fallacies("Some text.")

        assert result is None

    @patch("app.services.fallacy_analyzer.OpenAI")
    def test_uses_30s_timeout(self, mock_openai_class: MagicMock) -> None:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = _make_valid_response_json()
        mock_client.chat.completions.create.return_value = mock_response

        analyze_fallacies("Some text.")

        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs.get("timeout") == 30
