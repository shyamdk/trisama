from datetime import date, timedelta

from .models import DailyCheckIn, FinanceSnapshot, FoodLog, HabitLog, HealthMetric


def clamp_score(value: float, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(maximum, round(value)))


def calculate_category_scores(
    checkins: list[DailyCheckIn],
    health: list[HealthMetric],
    habits: list[HabitLog],
    foods: list[FoodLog],
    finance: list[FinanceSnapshot],
) -> dict[str, int]:
    today = date.today()
    week_start = today - timedelta(days=6)
    recent_habits = [h for h in habits if h.entry_date >= week_start]
    recent_foods = [f for f in foods if f.entry_date >= week_start]
    recent_checkins = [c for c in checkins if c.entry_date >= week_start]
    recent_health = [h for h in health if h.entry_date >= week_start]

    health_score = 40
    if recent_health:
        health_score += min(35, len(recent_health) * 5)
    if any(h.weight_kg for h in recent_health):
        health_score += 10
    if any(h.systolic_bp and h.diastolic_bp for h in recent_health):
        health_score += 15

    food_score = 50
    if recent_foods:
        avg_quality = sum((f.quality_score or 50) for f in recent_foods) / len(recent_foods)
        food_score = avg_quality
        food_score -= sum(10 for f in recent_foods if f.processed)
        food_score -= sum(8 for f in recent_foods if f.direct_sugar)
        food_score -= sum(6 for f in recent_foods if f.refined)

    exercise_habits = [h for h in recent_habits if h.category in {"exercise", "mind"}]
    exercise_score = 35
    if exercise_habits:
        completion_rate = sum(1 for h in exercise_habits if h.completed) / len(exercise_habits)
        exercise_score = 35 + completion_rate * 65

    sleep_habits = [h for h in recent_habits if h.category == "sleep"]
    sleep_score = 50
    if sleep_habits:
        sleep_score = 35 + (sum(1 for h in sleep_habits if h.completed) / len(sleep_habits)) * 65

    finance_score = 45
    if finance:
        finance_score += 25
    if any(item.kind == "investment" and item.monthly_cashflow and item.monthly_cashflow > 0 for item in finance):
        finance_score += 15
    if any(item.kind == "insurance" and item.renewal_date for item in finance):
        finance_score += 10

    social_habits = [h for h in recent_habits if h.category == "social"]
    social_score = 45
    if social_habits:
        social_score = 35 + (sum(1 for h in social_habits if h.completed) / len(social_habits)) * 65

    career_habits = [h for h in recent_habits if h.category in {"career", "growth"}]
    career_score = 45
    if career_habits:
        career_score = 35 + (sum(1 for h in career_habits if h.completed) / len(career_habits)) * 65

    accountability_score = 30 + min(40, len(recent_checkins) * 6) + min(30, len(recent_health) * 4)

    return {
        "health": clamp_score(health_score),
        "food": clamp_score(food_score),
        "exercise": clamp_score(exercise_score),
        "sleep": clamp_score(sleep_score),
        "finance": clamp_score(finance_score),
        "social": clamp_score(social_score),
        "career_growth": clamp_score(career_score),
        "accountability": clamp_score(accountability_score),
    }


def calculate_life_score(category_scores: dict[str, int]) -> int:
    weighted = (
        category_scores["health"] * 0.30
        + category_scores["food"] * 0.25
        + category_scores["exercise"] * 0.20
        + category_scores["sleep"] * 0.10
        + category_scores["finance"] * 0.05
        + category_scores["social"] * 0.05
        + category_scores["career_growth"] * 0.05
    )
    return clamp_score(weighted * 10, 0, 1000)


def summarize_finance(finance: list[FinanceSnapshot]) -> dict[str, float]:
    liquid_kinds = {"bank_account", "cash", "fd", "investment"}
    illiquid_kinds = {"property", "pf_retirement", "insurance"}

    total_assets = sum(item.value for item in finance)
    total_liabilities = sum(item.liability_value for item in finance)
    liquid_assets = sum(item.value for item in finance if item.kind in liquid_kinds)
    illiquid_assets = sum(item.value for item in finance if item.kind in illiquid_kinds)
    monthly_investments = sum(
        item.monthly_cashflow or 0 for item in finance if item.kind in {"investment", "pf_retirement"}
    )
    monthly_expenses = abs(
        sum(item.monthly_cashflow or 0 for item in finance if item.kind in {"expense", "liability"})
    )

    return {
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "net_worth": total_assets - total_liabilities,
        "liquid_assets": liquid_assets,
        "illiquid_assets": illiquid_assets,
        "monthly_investments": monthly_investments,
        "monthly_expenses": monthly_expenses,
    }


def build_coach_brief(
    category_scores: dict[str, int],
    latest_health: HealthMetric | None,
    checkins: list[DailyCheckIn],
    foods: list[FoodLog],
    finance: list[FinanceSnapshot],
) -> dict[str, list[str]]:
    wins: list[str] = []
    risks: list[str] = []
    missing_logs: list[str] = []
    next_actions: list[str] = []

    if category_scores["accountability"] >= 70:
        wins.append("Logging consistency is building.")
    if category_scores["exercise"] >= 70:
        wins.append("Exercise and mind habits are on track.")
    if category_scores["finance"] >= 70:
        wins.append("Finance snapshots are giving useful visibility.")

    if not checkins:
        missing_logs.append("Daily check-in")
    if not latest_health:
        missing_logs.append("Weight and BP")
    if not foods:
        missing_logs.append("Food log")
    if not finance:
        missing_logs.append("Finance snapshot")

    if latest_health and latest_health.systolic_bp and latest_health.systolic_bp >= 140:
        risks.append("BP reading is elevated. Track calmly and discuss repeated abnormal readings with a doctor.")
    if category_scores["food"] < 50:
        risks.append("Food quality is pulling the Life Score down.")
    if category_scores["sleep"] < 50:
        risks.append("Sleep consistency needs attention.")
    if category_scores["finance"] < 55:
        risks.append("Finance tracking is incomplete, so net worth insight is weak.")

    if "Weight and BP" in missing_logs:
        next_actions.append("Log today's weight and BP before the end of the day.")
    if category_scores["exercise"] < 70:
        next_actions.append("Complete a 15-minute walk, pranayama, meditation, or yoga block today.")
    if category_scores["food"] < 70:
        next_actions.append("Log the next meal with quantity and food quality score.")
    if category_scores["finance"] < 70:
        next_actions.append("Add one current bank, investment, PF, insurance, property, or liability snapshot.")

    return {
        "wins": wins[:3] or ["You have a clean starting point. Log honestly today."],
        "risks": risks[:3] or ["No major risk detected from the available logs."],
        "missing_logs": missing_logs[:4],
        "next_actions": next_actions[:3],
    }

