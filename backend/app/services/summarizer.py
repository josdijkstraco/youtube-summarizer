from openai import OpenAI

from app.config import settings

_MODEL = "gpt-4o-mini"
_TIMEOUT = 30

# Approximate token limit for a single API call.
# GPT-4o-mini supports 128K input tokens; we leave headroom for the system prompt.
# ~4 chars per token, so 100K tokens ≈ 400K chars.
_MAX_CHARS_PER_CHUNK = 400_000

_SYSTEM_PROMPT = (
    "You are a helpful assistant that summarizes YouTube video transcripts. "
    "Provide a clear, concise summary that captures the key points and main ideas. "
    "Use well-structured paragraphs. Do not include timestamps."
)

_COMBINE_SYSTEM_PROMPT = (
    "You are a helpful assistant. Combine the following partial summaries of a "
    "YouTube video transcript into one coherent, concise summary. "
    "Remove redundancies and present the information clearly."
)


def generate_summary(transcript_text: str) -> str:
    """Generate a summary of a YouTube video transcript using OpenAI.

    For transcripts exceeding the token limit, uses chunked summarization:
    splits the transcript into chunks, summarizes each, then combines.

    Args:
        transcript_text: The full transcript text.

    Returns:
        The generated summary string.
    """
    client = OpenAI(api_key=settings.openai_api_key)

    if len(transcript_text) <= _MAX_CHARS_PER_CHUNK:
        return _call_openai(client, _SYSTEM_PROMPT, transcript_text)

    # Chunked summarization for long transcripts
    chunks = _split_into_chunks(transcript_text, _MAX_CHARS_PER_CHUNK)
    chunk_summaries = [_call_openai(client, _SYSTEM_PROMPT, chunk) for chunk in chunks]

    combined = "\n\n".join(chunk_summaries)
    return _call_openai(client, _COMBINE_SYSTEM_PROMPT, combined)


def _call_openai(client: OpenAI, system_prompt: str, user_content: str) -> str:
    """Make a single OpenAI chat completion call."""
    response = client.chat.completions.create(
        model=_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        timeout=_TIMEOUT,
    )
    return response.choices[0].message.content or ""


def _split_into_chunks(text: str, max_chars: int) -> list[str]:
    """Split text into chunks at word boundaries."""
    chunks = []
    words = text.split()
    current_chunk: list[str] = []
    current_length = 0

    for word in words:
        word_len = len(word) + 1  # +1 for the space
        if current_length + word_len > max_chars and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(word)
        current_length += word_len

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks
