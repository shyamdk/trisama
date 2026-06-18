from datetime import date, datetime, time
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


def validate_log_entry_date(value: date) -> date:
    today = date.today()
    oldest_allowed = today.fromordinal(today.toordinal() - 2)
    if value < oldest_allowed:
        raise ValueError("Entry date can be at most 2 days before today")
    if value > today:
        raise ValueError("Entry date cannot be in the future")
    return value


class UserProfileOut(BaseModel):
    id: int
    name: str
    email: str | None
    role: str
    must_change_password: bool
    current_weight_kg: float
    daily_calorie_target: float
    bp_medication: str
    coaching_tone: str
    fasting_plan: str
    enabled_modules: str
    notes: str | None

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    role: str | None = None
    current_weight_kg: float | None = None
    daily_calorie_target: float | None = None
    bp_medication: str | None = None
    coaching_tone: str | None = None
    fasting_plan: str | None = None
    enabled_modules: str | None = None
    notes: str | None = None


class AdminUserCreate(BaseModel):
    name: str
    email: str
    role: str = "user"
    default_password: str = "ChangeMe@123"
    current_weight_kg: float = 118.0
    daily_calorie_target: float = 1800.0
    bp_medication: str = ""
    coaching_tone: str = "firm_practical"
    fasting_plan: str = "16:8"
    enabled_modules: str = '["health","food","exercise","sleep","social","career","bad_habits","finance","reminders"]'
    notes: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user: UserProfileOut


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class ForgotPasswordRequest(BaseModel):
    email: str


class ForgotPasswordResponse(BaseModel):
    message: str
    reset_token: str | None = None


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class AdminPasswordResetRequest(BaseModel):
    new_password: str = "ChangeMe@123"


class DailyCheckInCreate(BaseModel):
    user_id: int | None = None
    entry_date: date = Field(default_factory=date.today)
    mood: int | None = Field(default=None, ge=1, le=10)
    energy: int | None = Field(default=None, ge=1, le=10)
    stress: int | None = Field(default=None, ge=1, le=10)
    day_rating: int | None = Field(default=None, ge=1, le=10)
    notes: str | None = None


class DailyCheckInOut(DailyCheckInCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DailyChecklistItemOut(BaseModel):
    id: int
    user_id: int
    entry_date: date
    item_key: str
    label: str
    completed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DailyChecklistItemUpdate(BaseModel):
    completed: bool


class HealthMetricCreate(BaseModel):
    user_id: int | None = None
    entry_date: date = Field(default_factory=date.today)
    measurement_time: time | None = None
    weight_kg: float | None = None
    systolic_bp: int | None = None
    diastolic_bp: int | None = None
    blood_sugar: float | None = None
    sugar_context: str | None = None
    body_fat_percent: float | None = None
    muscle_percent: float | None = None
    visceral_fat: float | None = None
    body_age: float | None = None
    bmr: float | None = None
    notes: str | None = None


class HealthMetricOut(HealthMetricCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class HabitLogCreate(BaseModel):
    user_id: int | None = None
    entry_date: date = Field(default_factory=date.today)
    category: str
    name: str
    value: float | None = None
    unit: str | None = None
    target: float | None = None
    completed: bool = False
    notes: str | None = None


class HabitLogOut(HabitLogCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class FoodLogCreate(BaseModel):
    user_id: int | None = None
    entry_date: date = Field(default_factory=date.today)
    meal_time: time | None = None
    meal_type: str
    food_item: str = ""
    fasting_type: str | None = None
    fasting_hours: float | None = Field(default=None, ge=0, le=48)
    eating_window_hours: float | None = Field(default=None, ge=0, le=24)
    quantity_grams: float | None = None
    calories: float | None = None
    protein: float | None = None
    carbs: float | None = None
    fat: float | None = None
    fibre: float | None = None
    quality_score: int | None = Field(default=None, ge=0, le=100)
    processed: bool = False
    direct_sugar: bool = False
    refined: bool = False
    ai_enriched: bool = False
    ai_ingredients: str | None = None
    ai_risk_flags: str | None = None
    ai_notes: str | None = None
    notes: str | None = None


class FoodLogOut(FoodLogCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class FoodAnalyzeRequest(BaseModel):
    meal_type: str = ""
    food_item: str
    notes: str | None = None


class FoodAnalyzeOut(BaseModel):
    quantity_grams: float | None = None
    calories: float | None = None
    protein: float | None = None
    carbs: float | None = None
    fat: float | None = None
    fibre: float | None = None
    quality_score: int | None = None
    comments: str = ""
    ai_risk_flags: list[str] = []
    ai_ingredients: list[dict[str, Any]] = []


class FinanceSnapshotCreate(BaseModel):
    user_id: int | None = None
    entry_date: date = Field(default_factory=date.today)
    kind: str
    name: str
    value: float = 0
    liability_value: float = 0
    monthly_cashflow: float | None = None
    renewal_date: date | None = None
    notes: str | None = None


class FinanceSnapshotOut(FinanceSnapshotCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ReminderCreate(BaseModel):
    user_id: int | None = None
    title: str
    category: str
    due_date: date | None = None
    cadence: str | None = None
    channel: str = "app"
    completed: bool = False
    notes: str | None = None


class ReminderOut(ReminderCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DropdownOptionCreate(BaseModel):
    dropdown_key: str = Field(min_length=1, max_length=80)
    value: str = Field(min_length=1, max_length=160)
    label: str | None = Field(default=None, max_length=160)
    sort_order: int | None = None


class DropdownOptionOut(BaseModel):
    id: int
    dropdown_key: str
    value: str
    label: str
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ChallengeCreate(BaseModel):
    user_id: int | None = None
    title: str = "21 Day Challenge"
    start_date: date
    end_date: date
    target_weight_kg: float
    notes: str | None = None

    @model_validator(mode="after")
    def date_window(self) -> "ChallengeCreate":
        if self.end_date < self.start_date:
            raise ValueError("End date must be on or after start date")
        if (self.end_date - self.start_date).days > 60:
            raise ValueError("Challenge range cannot exceed 60 days")
        return self


class ChallengeOut(ChallengeCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ChallengeDayOut(BaseModel):
    entry_date: date
    weight_kg: float | None = None
    sugar: float | None = None
    sugar_context: str | None = None
    sugar_time: time | None = None


class ChallengeReportOut(ChallengeOut):
    days: list[ChallengeDayOut]


class DailyConsolidatedReportOut(BaseModel):
    entry_date: date
    weight_kg: float | None = None
    bp: str | None = None
    sugar: float | None = None
    sugar_context: str | None = None
    sugar_time: time | None = None
    body_fat_percent: float | None = None
    muscle_percent: float | None = None
    visceral_fat: float | None = None
    body_age: float | None = None
    bmr: float | None = None
    food_count: int = 0
    total_calories: float | None = None
    avg_quality_score: float | None = None
    food_items: list[str] = []
    food_flags: list[str] = []
    habits_done: int = 0
    habits_total: int = 0
    habit_items: list[str] = []
    finance_items: list[str] = []
    reminder_items: list[str] = []
    notes: list[str] = []


class CoachBrief(BaseModel):
    wins: list[str]
    risks: list[str]
    missing_logs: list[str]
    next_actions: list[str]


class DashboardOut(BaseModel):
    life_score: int
    accountability_score: int
    category_scores: dict[str, int]
    current_weight_kg: float | None
    latest_bp: str | None
    total_assets: float
    total_liabilities: float
    net_worth: float
    liquid_assets: float
    illiquid_assets: float
    monthly_investments: float
    monthly_expenses: float
    coach: CoachBrief


class ReportOut(BaseModel):
    period: str
    life_score: int
    accountability_score: int
    category_scores: dict[str, int]
    trends: list[str]
    risks: list[str]
    recommendations: list[str]
    finance_summary: dict[str, float]
    challenges: list[ChallengeReportOut] = []
    daily_reports: list[DailyConsolidatedReportOut] = []
