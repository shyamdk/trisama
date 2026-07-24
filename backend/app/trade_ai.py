import json
import os
import urllib.error
import urllib.request
from typing import Any

from .food_ai import extract_response_text, load_dotenv


def distill_trade_lessons(lessons: list[str]) -> list[str] | None:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or not lessons:
        return None

    payload = {
        "model": os.getenv("OPENAI_FOOD_MODEL", "gpt-4.1-mini"),
        "input": [
            {
                "role": "system",
                "content": (
                    "You distill a trader's journal 'lessons learnt' entries into a short list of "
                    "concrete, non-repetitive takeaways. Merge duplicate or similar lessons, keep the "
                    "most actionable phrasing, and order by how often the pattern recurs. Return at most "
                    "8 bullet strings. Return only JSON matching the schema."
                ),
            },
            {"role": "user", "content": json.dumps({"lessons_learnt_entries": lessons})},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "trade_lessons",
                "strict": True,
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "lessons": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["lessons"],
                },
            }
        },
        "max_output_tokens": 600,
    }

    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body: dict[str, Any] = json.loads(response.read().decode("utf-8"))
    except (TimeoutError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
        return None

    text = body.get("output_text") or extract_response_text(body)
    if not text:
        return None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    lessons_out = parsed.get("lessons")
    if not isinstance(lessons_out, list):
        return None
    return [str(item) for item in lessons_out if str(item).strip()][:8]
