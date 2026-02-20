import json
import logging

from openai import OpenAI

from app.config import settings
from app.models import FallacyAnalysisResult

logger = logging.getLogger(__name__)

_MODEL = "gpt-4o-mini"
_TIMEOUT = 30

_FALLACY_SYSTEM_PROMPT = (
    "You are an expert in logic, rhetoric, and critical thinking. "
    "Analyze the following transcript for logical fallacies.\n\n"
    "For each fallacy you identify:\n"
    "1. Quote the exact passage (keep it brief—just the relevant sentence or two)\n"
    "2. Name the fallacy\n"
    "3. Categorize it (Relevance, Presumption, Ambiguity, Emotional Appeal, "
    "Statistical, Manipulation)\n"
    "4. Rate severity: high (clearly flawed and potentially harmful), "
    "medium (problematic but subtle), low (minor or borderline)\n"
    "5. Explain in 2-3 sentences why this qualifies as a fallacy\n"
    "6. Provide a clearer example of the same fallacy pattern "
    "in a different context\n\n"
    "Be conservative. Not every rhetorical flourish is a fallacy. "
    "Look for arguments where the reasoning is genuinely flawed, "
    "not just where you disagree with the conclusion.\n\n"
    "Respond in JSON format:\n"
    "{\n"
    '  "summary": {\n'
    '    "total_fallacies": number,\n'
    '    "high_severity": number,\n'
    '    "medium_severity": number,\n'
    '    "low_severity": number,\n'
    '    "primary_tactics": ["list of most common fallacy types used"]\n'
    "  },\n"
    '  "fallacies": [\n'
    "    {\n"
    '      "timestamp": "if available, otherwise null",\n'
    '      "quote": "exact text",\n'
    '      "fallacy_name": "name",\n'
    '      "category": "category",\n'
    '      "severity": "high|medium|low",\n'
    '      "explanation": "why this is a fallacy",\n'
    '      "clear_example": {\n'
    '        "scenario": "a simpler example of the same pattern",\n'
    '        "why_wrong": "brief explanation"\n'
    "      }\n"
    "    }\n"
    "  ]\n"
    "}"
)


def analyze_fallacies(transcript_text: str) -> FallacyAnalysisResult | None:
    """Analyze a transcript for logical fallacies using OpenAI.

    Returns FallacyAnalysisResult on success, None on any failure.
    """
    try:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": _FALLACY_SYSTEM_PROMPT},
                {"role": "user", "content": transcript_text},
            ],
            response_format={"type": "json_object"},
            timeout=_TIMEOUT,
        )
        raw = response.choices[0].message.content or ""
        data = json.loads(raw)
        return FallacyAnalysisResult(**data)
    except Exception:
        logger.warning("Fallacy analysis failed", exc_info=True)
        return None
