"""Config-driven query classification."""

import json
import re

from app.config import get_settings
from app.generation.llm import get_llm_client
from app.platform.config_loader import get_platform_config


def _build_classification_prompt(query: str) -> str:
    cfg = get_platform_config()
    categories = [qt["name"] for qt in cfg.get_query_types()]
    category_list = "\n".join(f"- {c}" for c in categories)
    return f"""Classify the following enterprise query into exactly one category:
{category_list}

Query: {query}

Respond with JSON only: {{"query_type": "<category>"}}"""


def classify_query_keyword(query: str) -> str:
    cfg = get_platform_config()
    q = query.lower()
    for qt in cfg.get_query_types():
        keywords = qt.get("keywords", [])
        if keywords and any(kw in q for kw in keywords):
            return qt["name"]
    return cfg.routing.get("default_query_type", "General Search")


def classify_query(query: str) -> str:
    settings = get_settings()
    if settings.use_mock_llm or not settings.openai_api_key:
        return classify_query_keyword(query)

    try:
        client = get_llm_client()
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": _build_classification_prompt(query)}],
            temperature=0,
            max_tokens=50,
        )
        content = response.choices[0].message.content or ""
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            data = json.loads(match.group())
            type_str = data.get("query_type", "")
            valid = {qt["name"] for qt in get_platform_config().get_query_types()}
            if type_str in valid:
                return type_str
    except Exception:
        pass
    return classify_query_keyword(query)
