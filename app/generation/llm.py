"""LLM answer generation with grounded prompting."""

from openai import OpenAI

from app.config import get_settings

ANSWER_PROMPT = """You are an enterprise AI assistant. Answer ONLY using the provided context.
If information is unavailable, say: "I could not find sufficient information."
Do not hallucinate. Be concise and factual.

Context:
{context}

Question: {query}

Provide a clear, grounded answer based solely on the context above."""


def get_llm_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(api_key=settings.openai_api_key or "sk-mock")


def generate_answer_mock(query: str, context: str) -> str:
    """Fallback answer generation without LLM API."""
    if not context.strip():
        return "I could not find sufficient information."
    lines = [l.strip() for l in context.split("\n") if l.strip()][:5]
    summary = " ".join(lines)[:500]
    return f"Based on the retrieved enterprise documents: {summary}"


def generate_answer(query: str, context: str) -> str:
    settings = get_settings()
    if settings.use_mock_llm or not settings.openai_api_key:
        return generate_answer_mock(query, context)

    try:
        client = get_llm_client()
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {
                    "role": "user",
                    "content": ANSWER_PROMPT.format(context=context, query=query),
                }
            ],
            temperature=0.1,
            max_tokens=500,
        )
        return response.choices[0].message.content or "I could not find sufficient information."
    except Exception:
        return generate_answer_mock(query, context)
