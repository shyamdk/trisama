import json
import os
from pathlib import Path
import urllib.error
import urllib.request
from typing import Any


FOOD_RISK_FLAGS = [
    "simple_carbs",
    "rice",
    "chapati",
    "biscuits",
    "sweets",
    "bakery_items",
    "fruit_juice",
    "sugary_tea_coffee",
    "chips",
    "fried_snacks",
]
ENV_LOADED = False


def enrich_food_log(food_item: str, meal_type: str, notes: str | None = None) -> dict[str, Any] | None:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or not food_item.strip():
        return None

    prompt = {
        "meal_type": meal_type,
        "food_item": food_item,
        "notes": notes or "",
        "risk_flags_to_check": FOOD_RISK_FLAGS,
    }
    payload = {
        "model": os.getenv("OPENAI_FOOD_MODEL", "gpt-4.1-mini"),
        "input": [
            {
                "role": "system",
                "content": (
                    "You estimate Indian meal nutrition from short user food logs. "
                    "Extract each ingredient and quantity from text such as 'boiled egg (3), veges (100 gms)'. "
                    "If quantity is missing, make a conservative common-serving estimate. "
                    "Return only JSON matching the schema. Nutrition values are approximate. "
                    "quality_score must be an integer from 0 to 100."
                ),
            },
            {"role": "user", "content": json.dumps(prompt)},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "food_analysis",
                "strict": True,
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "ingredients": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "name": {"type": "string"},
                                    "quantity_text": {"type": "string"},
                                    "estimated_weight_grams": {"type": "number"},
                                    "calories": {"type": "number"},
                                    "protein": {"type": "number"},
                                    "carbs": {"type": "number"},
                                    "fat": {"type": "number"},
                                    "fibre": {"type": "number"},
                                },
                                "required": [
                                    "name",
                                    "quantity_text",
                                    "estimated_weight_grams",
                                    "calories",
                                    "protein",
                                    "carbs",
                                    "fat",
                                    "fibre",
                                ],
                            },
                        },
                        "total_weight_grams": {"type": "number"},
                        "calories": {"type": "number"},
                        "protein": {"type": "number"},
                        "carbs": {"type": "number"},
                        "fat": {"type": "number"},
                        "fibre": {"type": "number"},
                        "quality_score": {"type": "integer", "minimum": 0, "maximum": 100},
                        "risk_flags": {
                            "type": "array",
                            "items": {"type": "string", "enum": FOOD_RISK_FLAGS},
                        },
                        "notes": {"type": "string"},
                    },
                    "required": [
                        "ingredients",
                        "total_weight_grams",
                        "calories",
                        "protein",
                        "carbs",
                        "fat",
                        "fibre",
                        "quality_score",
                        "risk_flags",
                        "notes",
                    ],
                },
            }
        },
        "max_output_tokens": 1200,
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
            body = json.loads(response.read().decode("utf-8"))
    except (TimeoutError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
        return None

    text = body.get("output_text") or extract_response_text(body)
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def extract_response_text(body: dict[str, Any]) -> str | None:
    for item in body.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                return content["text"]
    return None


def apply_food_enrichment(payload: dict[str, Any], analysis: dict[str, Any] | None) -> dict[str, Any]:
    if not analysis:
        return payload

    risk_flags = [flag for flag in analysis.get("risk_flags", []) if flag in FOOD_RISK_FLAGS]
    payload["quantity_grams"] = payload.get("quantity_grams") or round_float(analysis.get("total_weight_grams"))
    payload["calories"] = payload.get("calories") or round_float(analysis.get("calories"))
    payload["protein"] = payload.get("protein") or round_float(analysis.get("protein"))
    payload["carbs"] = payload.get("carbs") or round_float(analysis.get("carbs"))
    payload["fat"] = payload.get("fat") or round_float(analysis.get("fat"))
    payload["fibre"] = payload.get("fibre") or round_float(analysis.get("fibre"))
    payload["quality_score"] = payload.get("quality_score") or normalize_quality_score(analysis.get("quality_score"))
    payload["ai_ingredients"] = json.dumps(analysis.get("ingredients", []))
    payload["ai_risk_flags"] = json.dumps(risk_flags)
    payload["ai_notes"] = analysis.get("notes")
    payload["ai_enriched"] = True

    payload["direct_sugar"] = payload.get("direct_sugar") or bool(
        {"sweets", "fruit_juice", "sugary_tea_coffee"} & set(risk_flags)
    )
    payload["refined"] = payload.get("refined") or bool(
        {"simple_carbs", "rice", "chapati", "biscuits", "bakery_items"} & set(risk_flags)
    )
    payload["processed"] = payload.get("processed") or bool(
        {"biscuits", "sweets", "bakery_items", "chips", "fried_snacks"} & set(risk_flags)
    )
    return payload


def food_analysis_for_form(analysis: dict[str, Any]) -> dict[str, Any]:
    risk_flags = [flag for flag in analysis.get("risk_flags", []) if flag in FOOD_RISK_FLAGS]
    ingredients = analysis.get("ingredients", [])
    comments = analysis.get("notes") or ""
    if risk_flags:
        comments = f"{comments} Flags: {', '.join(risk_flags)}.".strip()
    if ingredients:
        ingredient_lines = [
            f"{item.get('name', 'item')} ({item.get('quantity_text', '-')}, {round_float(item.get('estimated_weight_grams')) or '-'} g)"
            for item in ingredients
        ]
        comments = f"{comments}\nIngredients: {', '.join(ingredient_lines)}".strip()

    return {
        "quantity_grams": round_float(analysis.get("total_weight_grams")),
        "calories": round_float(analysis.get("calories")),
        "protein": round_float(analysis.get("protein")),
        "carbs": round_float(analysis.get("carbs")),
        "fat": round_float(analysis.get("fat")),
        "fibre": round_float(analysis.get("fibre")),
        "quality_score": normalize_quality_score(analysis.get("quality_score")),
        "comments": comments,
        "ai_risk_flags": risk_flags,
        "ai_ingredients": ingredients,
    }


def round_float(value: Any) -> float | None:
    if not isinstance(value, (int, float)):
        return None
    return round(float(value), 1)


def normalize_quality_score(value: Any) -> int | None:
    if not isinstance(value, (int, float)):
        return None
    score = float(value)
    if 0 <= score <= 10:
        score *= 10
    return max(0, min(100, round(score)))


def load_dotenv() -> None:
    global ENV_LOADED
    if ENV_LOADED:
        return
    ENV_LOADED = True
    env_path = Path.cwd() / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip("\"'")
