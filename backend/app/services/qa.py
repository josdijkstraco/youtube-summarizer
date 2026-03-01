from openai import AsyncOpenAI

from app.config import settings

_MODEL = "gpt-4o-mini"
_TIMEOUT = 30

_SYSTEM_PROMPT = (
    "You are a helpful assistant answering questions about a YouTube video transcript. "
    "Use only the transcript content to answer. Be concise and accurate.\n\n"
    "Transcript:\n{transcript}"
)


async def ask_question(transcript: str, question: str, history: list[dict]) -> str:
    messages: list[dict] = [
        {"role": "system", "content": _SYSTEM_PROMPT.format(transcript=transcript)}
    ]
    messages.extend(history)
    messages.append({"role": "user", "content": question})

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.chat.completions.create(
        model=_MODEL,
        messages=messages,  # type: ignore[arg-type]
        timeout=_TIMEOUT,
    )
    return response.choices[0].message.content or ""
