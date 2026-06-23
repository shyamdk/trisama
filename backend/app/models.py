from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, Float, Integer, String, Text, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), default="Primary User")
    email: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(40), default="user", index=True)
    password_hash: Mapped[str | None] = mapped_column(String(260), nullable=True)
    must_change_password: Mapped[bool] = mapped_column(default=True)
    password_reset_token: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    password_reset_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    current_weight_kg: Mapped[float] = mapped_column(Float, default=118.0)
    daily_calorie_target: Mapped[float] = mapped_column(Float, default=1800.0)
    bp_medication: Mapped[str] = mapped_column(String(120), default="Tazloc CT 40")
    coaching_tone: Mapped[str] = mapped_column(String(80), default="firm_practical")
    fasting_plan: Mapped[str] = mapped_column(String(40), default="16:8")
    enabled_modules: Mapped[str] = mapped_column(
        Text,
        default='["health","food","exercise","sleep","career","bad_habits","reminders","journal","expense_tracker","meds"]',
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class DailyCheckIn(Base, TimestampMixin):
    __tablename__ = "daily_checkins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, default=1, index=True)
    entry_date: Mapped[date] = mapped_column(Date, index=True)
    feeling: Mapped[str | None] = mapped_column(String(120), nullable=True)
    mood: Mapped[int | None] = mapped_column(Integer, nullable=True)
    energy: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stress: Mapped[int | None] = mapped_column(Integer, nullable=True)
    day_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gratitude: Mapped[str | None] = mapped_column(Text, nullable=True)
    journal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class DailyChecklistItem(Base, TimestampMixin):
    __tablename__ = "daily_checklist_items"
    __table_args__ = (UniqueConstraint("user_id", "entry_date", "item_key", name="uq_daily_checklist_user_date_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, default=1, index=True)
    entry_date: Mapped[date] = mapped_column(Date, index=True)
    item_key: Mapped[str] = mapped_column(String(80), index=True)
    label: Mapped[str] = mapped_column(String(160))
    completed: Mapped[bool] = mapped_column(default=False)


class HealthMetric(Base, TimestampMixin):
    __tablename__ = "health_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, default=1, index=True)
    entry_date: Mapped[date] = mapped_column(Date, index=True)
    measurement_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    systolic_bp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    diastolic_bp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    blood_sugar: Mapped[float | None] = mapped_column(Float, nullable=True)
    sugar_context: Mapped[str | None] = mapped_column(String(40), nullable=True)
    body_fat_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    muscle_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    visceral_fat: Mapped[float | None] = mapped_column(Float, nullable=True)
    body_age: Mapped[float | None] = mapped_column(Float, nullable=True)
    bmr: Mapped[float | None] = mapped_column(Float, nullable=True)
    shite_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class HabitLog(Base, TimestampMixin):
    __tablename__ = "habit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, default=1, index=True)
    entry_date: Mapped[date] = mapped_column(Date, index=True)
    habit_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    target: Mapped[float | None] = mapped_column(Float, nullable=True)
    completed: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class FoodLog(Base, TimestampMixin):
    __tablename__ = "food_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, default=1, index=True)
    entry_date: Mapped[date] = mapped_column(Date, index=True)
    meal_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    meal_type: Mapped[str] = mapped_column(String(80))
    food_item: Mapped[str] = mapped_column(String(160))
    post_meal_walk_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    fasting_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    fasting_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    eating_window_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    quantity_grams: Mapped[float | None] = mapped_column(Float, nullable=True)
    calories: Mapped[float | None] = mapped_column(Float, nullable=True)
    protein: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbs: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat: Mapped[float | None] = mapped_column(Float, nullable=True)
    fibre: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processed: Mapped[bool] = mapped_column(default=False)
    direct_sugar: Mapped[bool] = mapped_column(default=False)
    refined: Mapped[bool] = mapped_column(default=False)
    ai_enriched: Mapped[bool] = mapped_column(default=False)
    ai_ingredients: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_risk_flags: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class FinanceSnapshot(Base, TimestampMixin):
    __tablename__ = "finance_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, default=1, index=True)
    entry_date: Mapped[date] = mapped_column(Date, index=True)
    kind: Mapped[str] = mapped_column(String(80), index=True)
    name: Mapped[str] = mapped_column(String(160))
    value: Mapped[float] = mapped_column(Float, default=0)
    liability_value: Mapped[float] = mapped_column(Float, default=0)
    monthly_cashflow: Mapped[float | None] = mapped_column(Float, nullable=True)
    renewal_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class ExpenseLog(Base, TimestampMixin):
    __tablename__ = "expense_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, default=1, index=True)
    expense_date: Mapped[date] = mapped_column(Date, index=True)
    expense_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    expense: Mapped[str] = mapped_column(String(160))
    expense_type: Mapped[str] = mapped_column(String(80), index=True)
    expense_category: Mapped[str] = mapped_column(String(40), index=True)
    expense_mode: Mapped[str] = mapped_column(String(80), index=True)
    cost: Mapped[float] = mapped_column(Float, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class MedLog(Base, TimestampMixin):
    __tablename__ = "med_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, default=1, index=True)
    med_date: Mapped[date] = mapped_column(Date, index=True)
    med_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    med_name: Mapped[str] = mapped_column(String(160), index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class Reminder(Base, TimestampMixin):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, default=1, index=True)
    title: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(80), index=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    cadence: Mapped[str | None] = mapped_column(String(80), nullable=True)
    channel: Mapped[str] = mapped_column(String(80), default="app")
    completed: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class DropdownOption(Base, TimestampMixin):
    __tablename__ = "dropdown_options"
    __table_args__ = (UniqueConstraint("dropdown_key", "value", name="uq_dropdown_option_key_value"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dropdown_key: Mapped[str] = mapped_column(String(80), index=True)
    value: Mapped[str] = mapped_column(String(160))
    label: Mapped[str] = mapped_column(String(160))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Challenge(Base, TimestampMixin):
    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, default=1, index=True)
    title: Mapped[str] = mapped_column(String(160), default="21 Day Challenge")
    start_date: Mapped[date] = mapped_column(Date, index=True)
    end_date: Mapped[date] = mapped_column(Date, index=True)
    target_weight_kg: Mapped[float] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    token: Mapped[str] = mapped_column(String(120), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
