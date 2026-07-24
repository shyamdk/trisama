import hashlib
import json
import os
import secrets
from calendar import monthrange
from datetime import date, datetime, timedelta
from typing import TypeVar

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine, get_db
from .food_ai import apply_food_enrichment, enrich_food_log, food_analysis_for_form
from .models import AuthSession, Challenge, DailyCheckIn, DailyChecklistItem, DropdownOption, ExpenseLog, FinanceSnapshot, FoodLog, HabitLog, HealthMetric, MedLog, RecurringTask, Reminder, TodoTask, TradeJournalEntry, UserProfile
from .telegram_notify import send_telegram_message
from .trade_ai import distill_trade_lessons
from .schemas import (
    AdminPasswordResetRequest,
    AdminUserCreate,
    ChangePasswordRequest,
    ChallengeCreate,
    ChallengeOut,
    ChallengeReportOut,
    DailyCheckInCreate,
    DailyCheckInOut,
    DailyChecklistItemOut,
    DailyChecklistItemUpdate,
    DashboardOut,
    DropdownOptionCreate,
    DropdownOptionOut,
    DropdownOptionUpdate,
    ExpenseLogCreate,
    ExpenseLogOut,
    FinanceSnapshotCreate,
    FinanceSnapshotOut,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    FoodLogCreate,
    FoodLogOut,
    FoodAnalyzeOut,
    FoodAnalyzeRequest,
    HabitLogCreate,
    HabitLogOut,
    HealthMetricCreate,
    HealthMetricOut,
    LoginRequest,
    LoginResponse,
    MedLogCreate,
    MedLogOut,
    ReminderCreate,
    ReminderOut,
    ReportOut,
    RecurringTaskCreate,
    RecurringTaskOut,
    ResetPasswordRequest,
    TodoTaskCreate,
    TodoTaskOut,
    TradeJournalEntryCreate,
    TradeJournalEntryOut,
    TradeLessonsInsightOut,
    UserProfileOut,
    UserProfileUpdate,
)
from .scoring import build_coach_brief, calculate_category_scores, calculate_life_score, summarize_finance


app = FastAPI(title="PLOS API", version="0.1.0")
scheduler = BackgroundScheduler()
CRITICAL_TASK_CATEGORY = "Critical"
DEFAULT_USER_ID = 1
DEFAULT_ADMIN_EMAIL = os.getenv("PLOS_DEFAULT_ADMIN_EMAIL")
DEFAULT_ADMIN_PASSWORD = os.getenv("PLOS_DEFAULT_ADMIN_PASSWORD")
SESSION_DAYS = 7
DEFAULT_ENABLED_MODULE_KEYS = ["health", "food", "exercise", "sleep", "career", "bad_habits", "reminders", "journal", "expense_tracker", "meds", "trade_journal", "todo"]
NEW_MODULE_KEYS = {"journal", "expense_tracker", "meds", "trade_journal", "todo"}
REMOVED_MODULE_KEYS = {"social", "finance"}
DEFAULT_ENABLED_MODULES = json.dumps(DEFAULT_ENABLED_MODULE_KEYS)
UserOwnedModel = TypeVar("UserOwnedModel", DailyCheckIn, DailyChecklistItem, HealthMetric, HabitLog, FoodLog, FinanceSnapshot, ExpenseLog, MedLog, Reminder, Challenge, TradeJournalEntry, TodoTask, RecurringTask)
DEFAULT_DAILY_CHECKLIST = [
    ("body_metrics", "Weight / body metrics"),
    ("bp", "BP check-in"),
    ("sugar", "Sugar check-in"),
    ("food", "Food log"),
    ("exercise", "Exercise / movement"),
    ("sleep", "Sleep log"),
    ("bad_habits", "Bad habits check"),
    ("journal", "Journal"),
]
POST_MEAL_WALK_REQUIRED_MEALS = {"Breakfast", "Lunch", "Dinner"}
DEFAULT_DROPDOWN_OPTIONS = {
    "role": ["user", "admin"],
    "coaching_tone": ["firm_practical", "gentle_supportive", "hard_accountability"],
    "fasting_plan": ["16:8", "18:6", "Full day", "Custom"],
    "sugar_context": ["Fasting", "PP", "Random"],
    "meal_type": ["Breakfast", "Lunch", "Dinner", "Snack", "Fasting"],
    "physical_exercise_name": ["Yoga", "Walking", "Cycling", "Strength Training", "Daily Steps"],
    "mind_exercise_name": ["Meditation", "Pranayama"],
    "spirit_exercise_name": ["Vishnu Sahasranamam"],
    "sleep_name": ["Sleep Duration", "Sleep Quality", "Bed Time Consistency"],
    "career_name": ["Job Application", "Interview", "Learning Session", "Networking"],
    "bad_habit_name": ["Direct Sugar", "Processed Food", "Refined Food", "Smoking", "Alcohol", "Social Media"],
    "expense_type": [
        "Groceries",
        "Food & Dining",
        "Rent",
        "Utilities",
        "Fuel",
        "Transport",
        "Medical",
        "Insurance",
        "Education",
        "Entertainment",
        "Shopping",
        "Travel",
        "Investments",
        "EMI/Loan",
        "Subscriptions",
        "Gifts & Donations",
        "Household",
        "Personal Care",
        "Clothing",
        "Electronics",
        "Fitness",
        "Health Supplements",
        "Mobile & Internet",
        "Electricity",
        "Water",
        "Gas",
        "Home Maintenance",
        "Vehicle Maintenance",
        "Parking",
        "Tolls",
        "Taxes",
        "Professional Fees",
        "Child Education",
        "Pet Care",
        "Charity",
        "Festivals",
        "Vacation",
        "Business Expenses",
        "Miscellaneous",
    ],
    "expense_category": ["need", "want", "give"],
    "expense_mode": ["UPI", "Credit Card", "Debit Card", "Cash", "Net Banking", "Wallet", "Auto Debit", "Cheque"],
    "trade_type": ["options", "equity"],
    "trade_outcome": ["profit", "loss"],
    "trade_feeling": ["Jittery and Tensed", "Relaxed"],
    "task_type": ["Personal", "Official"],
    "task_category": ["Urgent", "Important", "Critical"],
    "task_group": ["Operational", "Strategic", "Finance", "Certification"],
    "task_status": ["Open", "Cancelled", "Completed", "Not_Needed"],
    "task_frequency": ["daily", "weekly", "monthly", "yearly"],
    "med_name": ["Tazloc CT 40", "D3", "B12"],
    "reminder_category": ["health", "food", "exercise", "sleep", "insurance", "career"],
    "reminder_channel": ["app", "telegram"],
}
SUPPLEMENT_REMINDER_CATEGORY = "health"
SUPPLEMENT_REMINDER_CHANNEL = "app"
D3_MED_NAMES = {"D3"}
B12_MED_NAMES = {"B12", "Renerve Injection 100mg"}
D3_REMINDER_TITLE = "Take D3"
B12_REMINDER_TITLE = "Take B12 injection"

DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3010",
    "http://127.0.0.1:3010",
]


def cors_origins() -> list[str]:
    configured = os.getenv("PLOS_CORS_ORIGINS", "")
    extra = [origin.strip() for origin in configured.split(",") if origin.strip()]
    return [*DEFAULT_CORS_ORIGINS, *extra]


app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_origin_regex=os.getenv("PLOS_CORS_ORIGIN_REGEX", r"https?://[^/]+:(3000|3010)"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        ensure_user_columns(db)
        ensure_user(db)
        ensure_all_enabled_modules(db)
        ensure_dropdown_options(db)
        ensure_supplement_reminders(db)
        ensure_recurring_tasks_synced(db)
        db.commit()
    if not scheduler.running:
        scheduler.add_job(
            run_critical_task_reminders_job,
            CronTrigger(hour="7-19", minute=0),
            id="critical_task_reminders",
            replace_existing=True,
        )
        scheduler.start()


@app.on_event("shutdown")
def shutdown() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)


def run_critical_task_reminders_job() -> None:
    with SessionLocal() as db:
        send_critical_task_reminders(db)


def send_critical_task_reminders(db: Session) -> None:
    tasks = (
        db.query(TodoTask)
        .filter(TodoTask.task_category == CRITICAL_TASK_CATEGORY, TodoTask.task_status == "Open")
        .order_by(TodoTask.task_due.is_(None), TodoTask.task_due)
        .all()
    )
    if not tasks:
        return
    lines = ["Critical open tasks:"]
    for task in tasks:
        due = f" (due {task.task_due})" if task.task_due else ""
        lines.append(f"- {task.task}{due}")
    send_telegram_message("\n".join(lines))


def ensure_user(db: Session) -> UserProfile:
    profile = db.query(UserProfile).filter(UserProfile.id == DEFAULT_USER_ID).first()
    if profile:
        profile.email = profile.email or DEFAULT_ADMIN_EMAIL
        profile.role = "admin"
        if not profile.password_hash and DEFAULT_ADMIN_PASSWORD:
            profile.password_hash = hash_password(DEFAULT_ADMIN_PASSWORD)
        profile.must_change_password = True if profile.must_change_password is None else profile.must_change_password
        profile.enabled_modules = ensure_enabled_modules(profile.enabled_modules)
        return profile
    profile = db.query(UserProfile).first()
    if profile:
        profile.enabled_modules = ensure_enabled_modules(profile.enabled_modules)
        return profile
    profile = UserProfile(
        id=DEFAULT_USER_ID,
        name="Primary User",
        email=DEFAULT_ADMIN_EMAIL,
        role="admin",
        password_hash=hash_password(DEFAULT_ADMIN_PASSWORD) if DEFAULT_ADMIN_PASSWORD else None,
        must_change_password=True,
        current_weight_kg=118.0,
        daily_calorie_target=1800.0,
        bp_medication="Tazloc CT 40",
        coaching_tone="firm_practical",
        fasting_plan="16:8",
        enabled_modules=DEFAULT_ENABLED_MODULES,
        notes="Default seeded user for local Phase 1 testing.",
    )
    db.add(profile)
    db.flush()
    return profile


def ensure_enabled_modules(enabled_modules: str | None) -> str:
    if not enabled_modules:
        return DEFAULT_ENABLED_MODULES
    try:
        enabled = json.loads(enabled_modules)
    except json.JSONDecodeError:
        return DEFAULT_ENABLED_MODULES
    if not isinstance(enabled, list):
        return DEFAULT_ENABLED_MODULES
    normalized = []
    for item in enabled:
        module = str(item)
        if module in REMOVED_MODULE_KEYS:
            continue
        if module not in normalized:
            normalized.append(module)
    for module in NEW_MODULE_KEYS:
        if module not in normalized:
            normalized.append(module)
    return json.dumps(normalized)


def ensure_all_enabled_modules(db: Session) -> None:
    for profile in db.query(UserProfile).all():
        profile.enabled_modules = ensure_enabled_modules(profile.enabled_modules)


def ensure_user_columns(db: Session) -> None:
    profile_columns = {row[1] for row in db.connection().exec_driver_sql("PRAGMA table_info(user_profiles)")}
    profile_alters = {
        "email": "ALTER TABLE user_profiles ADD COLUMN email VARCHAR(160)",
        "role": "ALTER TABLE user_profiles ADD COLUMN role VARCHAR(40) NOT NULL DEFAULT 'user'",
        "password_hash": "ALTER TABLE user_profiles ADD COLUMN password_hash VARCHAR(260)",
        "must_change_password": "ALTER TABLE user_profiles ADD COLUMN must_change_password BOOLEAN NOT NULL DEFAULT 1",
        "password_reset_token": "ALTER TABLE user_profiles ADD COLUMN password_reset_token VARCHAR(120)",
        "password_reset_expires_at": "ALTER TABLE user_profiles ADD COLUMN password_reset_expires_at DATETIME",
        "daily_calorie_target": "ALTER TABLE user_profiles ADD COLUMN daily_calorie_target FLOAT NOT NULL DEFAULT 1800",
        "fasting_plan": "ALTER TABLE user_profiles ADD COLUMN fasting_plan VARCHAR(40) NOT NULL DEFAULT '16:8'",
        "enabled_modules": f"ALTER TABLE user_profiles ADD COLUMN enabled_modules TEXT NOT NULL DEFAULT '{DEFAULT_ENABLED_MODULES}'",
    }
    for column, statement in profile_alters.items():
        if column not in profile_columns:
            db.connection().exec_driver_sql(statement)
    db.connection().exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_user_profiles_email ON user_profiles (email)")
    db.connection().exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_user_profiles_role ON user_profiles (role)")
    db.connection().exec_driver_sql(
        "CREATE INDEX IF NOT EXISTS ix_user_profiles_password_reset_token ON user_profiles (password_reset_token)"
    )

    tables = ["daily_checkins", "health_metrics", "habit_logs", "food_logs", "finance_snapshots", "reminders", "challenges"]
    for table in tables:
        columns = {row[1] for row in db.connection().exec_driver_sql(f"PRAGMA table_info({table})")}
        if "user_id" not in columns:
            db.connection().exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER NOT NULL DEFAULT {DEFAULT_USER_ID}")
            db.connection().exec_driver_sql(f"CREATE INDEX IF NOT EXISTS ix_{table}_user_id ON {table} (user_id)")

    food_columns = {row[1] for row in db.connection().exec_driver_sql("PRAGMA table_info(food_logs)")}
    food_alters = {
        "fasting_type": "ALTER TABLE food_logs ADD COLUMN fasting_type VARCHAR(40)",
        "meal_time": "ALTER TABLE food_logs ADD COLUMN meal_time TIME",
        "post_meal_walk_meters": "ALTER TABLE food_logs ADD COLUMN post_meal_walk_meters FLOAT",
        "fasting_hours": "ALTER TABLE food_logs ADD COLUMN fasting_hours FLOAT",
        "eating_window_hours": "ALTER TABLE food_logs ADD COLUMN eating_window_hours FLOAT",
        "ai_enriched": "ALTER TABLE food_logs ADD COLUMN ai_enriched BOOLEAN NOT NULL DEFAULT 0",
        "ai_ingredients": "ALTER TABLE food_logs ADD COLUMN ai_ingredients TEXT",
        "ai_risk_flags": "ALTER TABLE food_logs ADD COLUMN ai_risk_flags TEXT",
        "ai_notes": "ALTER TABLE food_logs ADD COLUMN ai_notes TEXT",
    }
    for column, statement in food_alters.items():
        if column not in food_columns:
            db.connection().exec_driver_sql(statement)

    checkin_columns = {row[1] for row in db.connection().exec_driver_sql("PRAGMA table_info(daily_checkins)")}
    checkin_alters = {
        "feeling": "ALTER TABLE daily_checkins ADD COLUMN feeling VARCHAR(120)",
        "gratitude": "ALTER TABLE daily_checkins ADD COLUMN gratitude TEXT",
        "journal_notes": "ALTER TABLE daily_checkins ADD COLUMN journal_notes TEXT",
    }
    for column, statement in checkin_alters.items():
        if column not in checkin_columns:
            db.connection().exec_driver_sql(statement)

    health_columns = {row[1] for row in db.connection().exec_driver_sql("PRAGMA table_info(health_metrics)")}
    if "measurement_time" not in health_columns:
        db.connection().exec_driver_sql("ALTER TABLE health_metrics ADD COLUMN measurement_time TIME")
    if "sugar_context" not in health_columns:
        db.connection().exec_driver_sql("ALTER TABLE health_metrics ADD COLUMN sugar_context VARCHAR(40)")
    if "shite_count" not in health_columns:
        db.connection().exec_driver_sql("ALTER TABLE health_metrics ADD COLUMN shite_count INTEGER")

    habit_columns = {row[1] for row in db.connection().exec_driver_sql("PRAGMA table_info(habit_logs)")}
    if "habit_time" not in habit_columns:
        db.connection().exec_driver_sql("ALTER TABLE habit_logs ADD COLUMN habit_time TIME")

    trade_journal_columns = {row[1] for row in db.connection().exec_driver_sql("PRAGMA table_info(trade_journal_entries)")}
    if "how_i_felt" not in trade_journal_columns:
        db.connection().exec_driver_sql("ALTER TABLE trade_journal_entries ADD COLUMN how_i_felt VARCHAR(80)")

    todo_task_columns = {row[1] for row in db.connection().exec_driver_sql("PRAGMA table_info(todo_tasks)")}
    if "recurring_task_id" not in todo_task_columns:
        db.connection().exec_driver_sql("ALTER TABLE todo_tasks ADD COLUMN recurring_task_id INTEGER")

    recurring_task_columns = {row[1] for row in db.connection().exec_driver_sql("PRAGMA table_info(recurring_tasks)")}
    if "day_of_week" not in recurring_task_columns:
        db.connection().exec_driver_sql("ALTER TABLE recurring_tasks ADD COLUMN day_of_week VARCHAR(20)")
    if "day_of_month" not in recurring_task_columns:
        db.connection().exec_driver_sql("ALTER TABLE recurring_tasks ADD COLUMN day_of_month INTEGER")
    if "month_of_year" not in recurring_task_columns:
        db.connection().exec_driver_sql("ALTER TABLE recurring_tasks ADD COLUMN month_of_year INTEGER")

    db.connection().exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_expense_logs_user_id ON expense_logs (user_id)")
    db.connection().exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_expense_logs_expense_date ON expense_logs (expense_date)")
    db.connection().exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_med_logs_user_id ON med_logs (user_id)")
    db.connection().exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_med_logs_med_date ON med_logs (med_date)")


def ensure_dropdown_options(db: Session) -> None:
    for dropdown_key, values in DEFAULT_DROPDOWN_OPTIONS.items():
        for index, value in enumerate(values):
            existing = (
                db.query(DropdownOption)
                .filter(DropdownOption.dropdown_key == dropdown_key, DropdownOption.value == value)
                .first()
            )
            if existing:
                continue
            db.add(
                DropdownOption(
                    dropdown_key=dropdown_key,
                    value=value,
                    label=value.replace("_", " "),
                    sort_order=index,
                )
            )


def ensure_supplement_reminders(db: Session) -> None:
    for profile in db.query(UserProfile).all():
        sync_supplement_reminders(db, profile.id)


def sync_supplement_reminders(db: Session, user_id: int) -> None:
    today = date.today()
    latest_d3 = latest_med_date(db, user_id, D3_MED_NAMES)
    latest_b12 = latest_med_date(db, user_id, B12_MED_NAMES)

    if latest_d3 or supplement_reminder_exists(db, user_id, D3_REMINDER_TITLE):
        d3_due_date = next_weekly_due_date(latest_d3, today)
        upsert_supplement_reminder(
            db,
            user_id=user_id,
            title=D3_REMINDER_TITLE,
            due_date=d3_due_date,
            cadence="weekly on Saturday",
            notes="Take D3 every Saturday. Log a D3 med entry after taking it so the next reminder moves forward.",
            today=today,
        )

    if latest_b12:
        b12_due_date = add_months(latest_b12, 2)
        upsert_supplement_reminder(
            db,
            user_id=user_id,
            title=B12_REMINDER_TITLE,
            due_date=b12_due_date,
            cadence="every 2 months from last injection",
            notes=f"Last B12 injection logged on {latest_b12.isoformat()}. Log each B12 injection so this due date stays accurate.",
            today=today,
        )


def latest_med_date(db: Session, user_id: int, med_names: set[str]) -> date | None:
    row = (
        user_query(db, MedLog, user_id)
        .filter(MedLog.med_name.in_(med_names))
        .order_by(desc(MedLog.med_date), desc(MedLog.created_at))
        .first()
    )
    return row.med_date if row else None


def supplement_reminder_exists(db: Session, user_id: int, title: str) -> bool:
    return user_query(db, Reminder, user_id).filter(Reminder.title == title).first() is not None


def next_weekly_due_date(latest_taken: date | None, today: date) -> date:
    if not latest_taken:
        return next_saturday_on_or_after(today)
    due_date = next_saturday_after(latest_taken)
    while due_date < today:
        due_date += timedelta(days=7)
    return due_date


def next_saturday_on_or_after(value: date) -> date:
    return value + timedelta(days=(5 - value.weekday()) % 7)


def next_saturday_after(value: date) -> date:
    days_until_saturday = (5 - value.weekday()) % 7
    if days_until_saturday == 0:
        days_until_saturday = 7
    return value + timedelta(days=days_until_saturday)


def add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)


def advance_recurring_due_date(value: date, frequency: str) -> date:
    if frequency == "daily":
        return value + timedelta(days=1)
    if frequency == "weekly":
        return value + timedelta(days=7)
    if frequency == "yearly":
        return add_months(value, 12)
    return add_months(value, 1)


WEEKDAY_INDEX = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}


def compute_recurring_due_date(
    frequency: str,
    day_of_week: str | None,
    day_of_month: int | None,
    month_of_year: int | None,
    today: date,
) -> date:
    if frequency == "weekly":
        target_weekday = WEEKDAY_INDEX.get(day_of_week or "Monday", 0)
        days_ahead = (target_weekday - today.weekday()) % 7
        return today + timedelta(days=days_ahead)
    if frequency == "monthly":
        day = max(1, min(day_of_month or 1, 31))
        candidate = date(today.year, today.month, min(day, monthrange(today.year, today.month)[1]))
        if candidate < today:
            candidate = add_months(candidate, 1)
        return candidate
    if frequency == "yearly":
        month = month_of_year or 1
        day = max(1, min(day_of_month or 1, 31))
        candidate = date(today.year, month, min(day, monthrange(today.year, month)[1]))
        if candidate < today:
            candidate = date(today.year + 1, month, min(day, monthrange(today.year + 1, month)[1]))
        return candidate
    return today


def ensure_recurring_tasks_synced(db: Session) -> None:
    for profile in db.query(UserProfile).all():
        sync_recurring_tasks(db, profile.id)


def sync_recurring_tasks(db: Session, user_id: int) -> None:
    today = date.today()
    templates = (
        user_query(db, RecurringTask, user_id)
        .filter(RecurringTask.task_status == "Open")
        .all()
    )
    for template in templates:
        iterations = 0
        while template.task_due and template.task_due <= today and iterations < 366:
            iterations += 1
            already_generated = (
                user_query(db, TodoTask, user_id)
                .filter(TodoTask.recurring_task_id == template.id, TodoTask.task_due == template.task_due)
                .first()
            )
            if not already_generated:
                db.add(
                    TodoTask(
                        user_id=user_id,
                        recurring_task_id=template.id,
                        task=template.task,
                        task_due=template.task_due,
                        task_type=template.task_type,
                        task_category=template.task_category,
                        task_group=template.task_group,
                        task_status="Open",
                        task_comments=template.task_comments,
                    )
                )
            template.task_due = advance_recurring_due_date(template.task_due, template.frequency)


def upsert_supplement_reminder(
    db: Session,
    *,
    user_id: int,
    title: str,
    due_date: date,
    cadence: str,
    notes: str,
    today: date,
) -> None:
    reminder = user_query(db, Reminder, user_id).filter(Reminder.title == title).first()
    if not reminder:
        db.add(
            Reminder(
                user_id=user_id,
                title=title,
                category=SUPPLEMENT_REMINDER_CATEGORY,
                due_date=due_date,
                cadence=cadence,
                channel=SUPPLEMENT_REMINDER_CHANNEL,
                completed=False,
                notes=notes,
            )
        )
        return

    due_changed = reminder.due_date != due_date
    reminder.category = SUPPLEMENT_REMINDER_CATEGORY
    reminder.due_date = due_date
    reminder.cadence = cadence
    reminder.channel = SUPPLEMENT_REMINDER_CHANNEL
    reminder.notes = notes
    if due_changed or due_date <= today:
        reminder.completed = False


def get_user(db: Session, user_id: int = DEFAULT_USER_ID) -> UserProfile:
    profile = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if profile:
        return profile
    return ensure_user(db)


def with_user(payload: dict, user_id: int) -> dict:
    payload["user_id"] = payload.get("user_id") or user_id
    return payload


def user_query(db: Session, model: type[UserOwnedModel], user_id: int):
    return db.query(model).filter(model.user_id == user_id)


def get_owned_item(db: Session, model: type[UserOwnedModel], user_id: int, item_id: int, label: str) -> UserOwnedModel:
    get_user(db, user_id)
    item = user_query(db, model, user_id).filter(model.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found")
    return item


def apply_payload(item: UserOwnedModel, payload: dict) -> None:
    for key, value in payload.items():
        if key == "user_id":
            continue
        setattr(item, key, value)


def require_post_meal_walk(food_payload: dict) -> None:
    meal_type = food_payload.get("meal_type")
    walk_meters = food_payload.get("post_meal_walk_meters")
    if meal_type in POST_MEAL_WALK_REQUIRED_MEALS and (walk_meters is None or walk_meters <= 0):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Post-meal walk distance in meters is required for Breakfast, Lunch, and Dinner.",
        )


def ensure_daily_checklist(db: Session, user_id: int, entry_date: date) -> list[DailyChecklistItem]:
    active_keys = {key for key, _label in DEFAULT_DAILY_CHECKLIST}
    existing = {
        item.item_key: item
        for item in user_query(db, DailyChecklistItem, user_id)
        .filter(DailyChecklistItem.entry_date == entry_date)
        .filter(DailyChecklistItem.item_key.in_(active_keys))
        .all()
    }
    for item_key, label in DEFAULT_DAILY_CHECKLIST:
        if item_key in existing:
            continue
        item = DailyChecklistItem(user_id=user_id, entry_date=entry_date, item_key=item_key, label=label, completed=False)
        db.add(item)
        existing[item_key] = item
    db.flush()
    return sorted(existing.values(), key=lambda item: [key for key, _label in DEFAULT_DAILY_CHECKLIST].index(item.item_key))


def infer_daily_checklist_completion(db: Session, user_id: int, entry_date: date) -> dict[str, bool]:
    health_rows = user_query(db, HealthMetric, user_id).filter(HealthMetric.entry_date == entry_date).all()
    habit_rows = user_query(db, HabitLog, user_id).filter(HabitLog.entry_date == entry_date).all()
    food_exists = (
        user_query(db, FoodLog, user_id)
        .filter(FoodLog.entry_date == entry_date)
        .first()
        is not None
    )
    habit_categories = {row.category for row in habit_rows}
    journal_exists = any(
        row.feeling or row.mood is not None or row.gratitude or row.journal_notes or row.notes
        for row in user_query(db, DailyCheckIn, user_id).filter(DailyCheckIn.entry_date == entry_date).all()
    )
    return {
        "body_metrics": any(
            value is not None
            for row in health_rows
            for value in [
                row.weight_kg,
                row.body_fat_percent,
                row.muscle_percent,
                row.visceral_fat,
                row.body_age,
                row.bmr,
            ]
        ),
        "bp": any(row.systolic_bp is not None and row.diastolic_bp is not None for row in health_rows),
        "sugar": any(row.blood_sugar is not None for row in health_rows),
        "food": food_exists,
        "exercise": bool(habit_categories & {"exercise", "mind"}),
        "sleep": "sleep" in habit_categories,
        "bad_habits": bool(habit_categories & {"bad_habit", "bad_habits"}),
        "journal": journal_exists,
    }


def sync_daily_checklist_completion(db: Session, user_id: int, entry_date: date) -> list[DailyChecklistItem]:
    rows = ensure_daily_checklist(db, user_id, entry_date)
    inferred = infer_daily_checklist_completion(db, user_id, entry_date)
    for item in rows:
        if inferred.get(item.item_key):
            item.completed = True
    db.flush()
    return rows


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000).hex()
    return f"pbkdf2_sha256${salt}${digest}"


def verify_password(password: str, stored_hash: str | None) -> bool:
    if not stored_hash:
        return False
    try:
        algorithm, salt, expected = stored_hash.split("$", 2)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000).hex()
    return secrets.compare_digest(digest, expected)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def create_session(db: Session, user: UserProfile) -> AuthSession:
    session = AuthSession(
        token=secrets.token_urlsafe(32),
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(days=SESSION_DAYS),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> UserProfile:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing session token")
    token = authorization.removeprefix("Bearer ").strip()
    session = db.query(AuthSession).filter(AuthSession.token == token).first()
    if not session or session.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
    user = db.query(UserProfile).filter(UserProfile.id == session.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session user not found")
    return user


def current_admin(user: UserProfile = Depends(current_user)) -> UserProfile:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def get_user_by_email(db: Session, email: str) -> UserProfile | None:
    return db.query(UserProfile).filter(UserProfile.email == normalize_email(email)).first()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict:
    user = get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    session = create_session(db, user)
    return {"token": session.token, "user": user}


@app.get("/auth/me", response_model=UserProfileOut)
def me(user: UserProfile = Depends(current_user)) -> UserProfile:
    return user


@app.post("/auth/change-password", response_model=UserProfileOut)
def change_password(
    payload: ChangePasswordRequest,
    user: UserProfile = Depends(current_user),
    db: Session = Depends(get_db),
) -> UserProfile:
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = False
    user.password_reset_token = None
    user.password_reset_expires_at = None
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> dict:
    user = get_user_by_email(db, payload.email)
    if not user:
        return {"message": "If the email exists, a reset token has been generated.", "reset_token": None}
    token = secrets.token_urlsafe(24)
    user.password_reset_token = token
    user.password_reset_expires_at = datetime.utcnow() + timedelta(hours=2)
    db.commit()
    return {
        "message": "Reset token generated. Local dev mode returns the token directly.",
        "reset_token": token,
    }


@app.post("/auth/reset-password", response_model=UserProfileOut)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> UserProfile:
    user = db.query(UserProfile).filter(UserProfile.password_reset_token == payload.token).first()
    if not user or not user.password_reset_expires_at or user.password_reset_expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = False
    user.password_reset_token = None
    user.password_reset_expires_at = None
    db.commit()
    db.refresh(user)
    return user


@app.get("/admin/users", response_model=list[UserProfileOut])
def admin_list_users(
    _admin: UserProfile = Depends(current_admin),
    db: Session = Depends(get_db),
) -> list[UserProfile]:
    return db.query(UserProfile).order_by(UserProfile.id).all()


@app.post("/admin/users", response_model=UserProfileOut)
def admin_create_user(
    payload: AdminUserCreate,
    _admin: UserProfile = Depends(current_admin),
    db: Session = Depends(get_db),
) -> UserProfile:
    email = normalize_email(payload.email)
    if get_user_by_email(db, email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
    if payload.role not in {"admin", "user"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role must be admin or user")
    user = UserProfile(
        name=payload.name,
        email=email,
        role=payload.role,
        password_hash=hash_password(payload.default_password),
        must_change_password=True,
        current_weight_kg=payload.current_weight_kg,
        daily_calorie_target=payload.daily_calorie_target,
        bp_medication=payload.bp_medication,
        coaching_tone=payload.coaching_tone,
        fasting_plan=payload.fasting_plan,
        enabled_modules=payload.enabled_modules,
        notes=payload.notes,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/admin/users/{user_id}/reset-password", response_model=ForgotPasswordResponse)
def admin_reset_user_password(
    user_id: int,
    payload: AdminPasswordResetRequest,
    _admin: UserProfile = Depends(current_admin),
    db: Session = Depends(get_db),
) -> dict:
    user = get_user(db, user_id)
    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = True
    user.password_reset_token = None
    user.password_reset_expires_at = None
    db.commit()
    return {
        "message": f"Password reset for {user.email or user.name}. User must change password after login.",
        "reset_token": None,
    }


@app.get("/dropdown-options", response_model=list[DropdownOptionOut])
def list_dropdown_options(db: Session = Depends(get_db)) -> list[DropdownOption]:
    return db.query(DropdownOption).order_by(DropdownOption.dropdown_key, DropdownOption.sort_order, DropdownOption.label).all()


@app.post("/admin/dropdown-options", response_model=DropdownOptionOut)
def admin_create_dropdown_option(
    payload: DropdownOptionCreate,
    _admin: UserProfile = Depends(current_admin),
    db: Session = Depends(get_db),
) -> DropdownOption:
    dropdown_key = payload.dropdown_key.strip()
    value = payload.value.strip()
    if not dropdown_key or not value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dropdown key and value are required")
    existing = db.query(DropdownOption).filter(DropdownOption.dropdown_key == dropdown_key, DropdownOption.value == value).first()
    if existing:
        return existing
    sort_order = payload.sort_order
    if sort_order is None:
        latest = (
            db.query(DropdownOption)
            .filter(DropdownOption.dropdown_key == dropdown_key)
            .order_by(desc(DropdownOption.sort_order))
            .first()
        )
        sort_order = (latest.sort_order + 1) if latest else 0
    item = DropdownOption(
        dropdown_key=dropdown_key,
        value=value,
        label=(payload.label or value).strip(),
        sort_order=sort_order,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.patch("/admin/dropdown-options/{option_id}", response_model=DropdownOptionOut)
def admin_update_dropdown_option(
    option_id: int,
    payload: DropdownOptionUpdate,
    _admin: UserProfile = Depends(current_admin),
    db: Session = Depends(get_db),
) -> DropdownOption:
    item = db.query(DropdownOption).filter(DropdownOption.id == option_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dropdown option not found")
    if payload.value is not None:
        value = payload.value.strip()
        if not value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dropdown option value is required")
        duplicate = (
            db.query(DropdownOption)
            .filter(DropdownOption.dropdown_key == item.dropdown_key, DropdownOption.value == value, DropdownOption.id != option_id)
            .first()
        )
        if duplicate:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dropdown option already exists")
        item.value = value
    if payload.label is not None:
        label = payload.label.strip()
        item.label = label or item.value
    if payload.sort_order is not None:
        item.sort_order = payload.sort_order
    db.commit()
    db.refresh(item)
    return item


@app.delete("/admin/dropdown-options/{option_id}", status_code=204)
def admin_delete_dropdown_option(
    option_id: int,
    _admin: UserProfile = Depends(current_admin),
    db: Session = Depends(get_db),
) -> None:
    item = db.query(DropdownOption).filter(DropdownOption.id == option_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dropdown option not found")
    db.delete(item)
    db.commit()


@app.get("/users", response_model=list[UserProfileOut])
def list_users(
    _admin: UserProfile = Depends(current_admin),
    db: Session = Depends(get_db),
) -> list[UserProfile]:
    return db.query(UserProfile).order_by(UserProfile.id).all()


@app.get("/users/{user_id}", response_model=UserProfileOut)
def get_user_profile(user_id: int, db: Session = Depends(get_db)) -> UserProfile:
    return get_user(db, user_id)


@app.patch("/users/{user_id}", response_model=UserProfileOut)
def update_user_profile(
    user_id: int,
    payload: UserProfileUpdate,
    auth_user: UserProfile = Depends(current_user),
    db: Session = Depends(get_db),
) -> UserProfile:
    if auth_user.id != user_id and auth_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot edit another user")
    profile = get_user(db, user_id)
    not_nullable_string_fields = {"name", "bp_medication", "coaching_tone", "fasting_plan", "enabled_modules"}
    for key, value in payload.model_dump(exclude_unset=True).items():
        if key == "role" and auth_user.role != "admin":
            continue
        if value is None and key in not_nullable_string_fields:
            value = ""
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile


@app.get("/profile", response_model=UserProfileOut)
def get_profile(db: Session = Depends(get_db)) -> UserProfile:
    return get_user(db)


@app.post("/checkins", response_model=DailyCheckInOut)
def create_checkin(payload: DailyCheckInCreate, user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> DailyCheckIn:
    get_user(db, user_id)
    item = DailyCheckIn(**with_user(payload.model_dump(), user_id))
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/checkins", response_model=list[DailyCheckInOut])
def list_checkins(user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> list[DailyCheckIn]:
    return user_query(db, DailyCheckIn, user_id).order_by(desc(DailyCheckIn.entry_date)).limit(30).all()


@app.patch("/checkins/{checkin_id}", response_model=DailyCheckInOut)
def update_checkin(
    checkin_id: int,
    payload: DailyCheckInCreate,
    user_id: int = Query(DEFAULT_USER_ID),
    db: Session = Depends(get_db),
) -> DailyCheckIn:
    item = get_owned_item(db, DailyCheckIn, user_id, checkin_id, "Journal entry")
    apply_payload(item, payload.model_dump())
    db.flush()
    sync_daily_checklist_completion(db, user_id, item.entry_date)
    db.commit()
    db.refresh(item)
    return item


@app.delete("/checkins/{checkin_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_checkin(checkin_id: int, user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> None:
    item = get_owned_item(db, DailyCheckIn, user_id, checkin_id, "Journal entry")
    db.delete(item)
    db.commit()


@app.get("/daily-checklist", response_model=list[DailyChecklistItemOut])
def get_daily_checklist(
    entry_date: date | None = Query(None),
    user_id: int = Query(DEFAULT_USER_ID),
    db: Session = Depends(get_db),
) -> list[DailyChecklistItem]:
    get_user(db, user_id)
    rows = sync_daily_checklist_completion(db, user_id, entry_date or date.today())
    db.commit()
    return rows


@app.patch("/daily-checklist/{item_key}", response_model=DailyChecklistItemOut)
def update_daily_checklist_item(
    item_key: str,
    payload: DailyChecklistItemUpdate,
    entry_date: date | None = Query(None),
    user_id: int = Query(DEFAULT_USER_ID),
    db: Session = Depends(get_db),
) -> DailyChecklistItem:
    get_user(db, user_id)
    checklist_date = entry_date or date.today()
    ensure_daily_checklist(db, user_id, checklist_date)
    item = (
        user_query(db, DailyChecklistItem, user_id)
        .filter(DailyChecklistItem.entry_date == checklist_date, DailyChecklistItem.item_key == item_key)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checklist item not found")
    item.completed = payload.completed
    db.commit()
    db.refresh(item)
    return item


@app.post("/health-metrics", response_model=HealthMetricOut)
def create_health_metric(payload: HealthMetricCreate, user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> HealthMetric:
    get_user(db, user_id)
    item = HealthMetric(**with_user(payload.model_dump(), user_id))
    db.add(item)
    db.flush()
    sync_daily_checklist_completion(db, user_id, item.entry_date)
    db.commit()
    db.refresh(item)
    return item


@app.get("/health-metrics", response_model=list[HealthMetricOut])
def list_health_metrics(user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> list[HealthMetric]:
    return user_query(db, HealthMetric, user_id).order_by(desc(HealthMetric.entry_date)).limit(30).all()


@app.patch("/health-metrics/{metric_id}", response_model=HealthMetricOut)
def update_health_metric(
    metric_id: int,
    payload: HealthMetricCreate,
    user_id: int = Query(DEFAULT_USER_ID),
    db: Session = Depends(get_db),
) -> HealthMetric:
    item = get_owned_item(db, HealthMetric, user_id, metric_id, "Health metric")
    apply_payload(item, payload.model_dump())
    db.flush()
    sync_daily_checklist_completion(db, user_id, item.entry_date)
    db.commit()
    db.refresh(item)
    return item


@app.delete("/health-metrics/{metric_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_health_metric(metric_id: int, user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> None:
    item = get_owned_item(db, HealthMetric, user_id, metric_id, "Health metric")
    db.delete(item)
    db.commit()


@app.post("/habits", response_model=HabitLogOut)
def create_habit(payload: HabitLogCreate, user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> HabitLog:
    get_user(db, user_id)
    item = HabitLog(**with_user(payload.model_dump(), user_id))
    db.add(item)
    db.flush()
    sync_daily_checklist_completion(db, user_id, item.entry_date)
    db.commit()
    db.refresh(item)
    return item


@app.get("/habits", response_model=list[HabitLogOut])
def list_habits(user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> list[HabitLog]:
    return user_query(db, HabitLog, user_id).order_by(desc(HabitLog.entry_date), desc(HabitLog.habit_time)).limit(100).all()


@app.patch("/habits/{habit_id}", response_model=HabitLogOut)
def update_habit(
    habit_id: int,
    payload: HabitLogCreate,
    user_id: int = Query(DEFAULT_USER_ID),
    db: Session = Depends(get_db),
) -> HabitLog:
    item = get_owned_item(db, HabitLog, user_id, habit_id, "Habit log")
    apply_payload(item, payload.model_dump())
    db.flush()
    sync_daily_checklist_completion(db, user_id, item.entry_date)
    db.commit()
    db.refresh(item)
    return item


@app.delete("/habits/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_habit(habit_id: int, user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> None:
    item = get_owned_item(db, HabitLog, user_id, habit_id, "Habit log")
    db.delete(item)
    db.commit()


@app.post("/foods", response_model=FoodLogOut)
def create_food(payload: FoodLogCreate, user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> FoodLog:
    get_user(db, user_id)
    food_payload = payload.model_dump()
    require_post_meal_walk(food_payload)
    profile = get_user(db, user_id)
    food_payload["fasting_type"] = profile.fasting_plan
    analysis = enrich_food_log(food_payload.get("food_item") or "", food_payload.get("meal_type") or "", food_payload.get("notes"))
    food_payload = apply_food_enrichment(food_payload, analysis)
    item = FoodLog(**with_user(food_payload, user_id))
    db.add(item)
    db.flush()
    sync_daily_checklist_completion(db, user_id, item.entry_date)
    db.commit()
    db.refresh(item)
    return item


@app.patch("/foods/{food_id}", response_model=FoodLogOut)
def update_food(
    food_id: int,
    payload: FoodLogCreate,
    user_id: int = Query(DEFAULT_USER_ID),
    db: Session = Depends(get_db),
) -> FoodLog:
    profile = get_user(db, user_id)
    item = user_query(db, FoodLog, user_id).filter(FoodLog.id == food_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food log not found")
    food_payload = payload.model_dump()
    require_post_meal_walk(food_payload)
    food_payload["fasting_type"] = profile.fasting_plan
    analysis = enrich_food_log(food_payload.get("food_item") or "", food_payload.get("meal_type") or "", food_payload.get("notes"))
    if analysis:
        food_payload = apply_food_enrichment(food_payload, analysis)
    else:
        for derived_key in [
            "quantity_grams",
            "protein",
            "carbs",
            "fat",
            "fibre",
        ]:
            if food_payload.get(derived_key) is None:
                food_payload[derived_key] = getattr(item, derived_key)
        for ai_key in ["ai_enriched", "ai_ingredients", "ai_risk_flags", "ai_notes"]:
            food_payload[ai_key] = getattr(item, ai_key)
    for key, value in food_payload.items():
        if key == "user_id":
            continue
        setattr(item, key, value)
    db.flush()
    sync_daily_checklist_completion(db, user_id, item.entry_date)
    db.commit()
    db.refresh(item)
    return item


@app.delete("/foods/{food_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_food(food_id: int, user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> None:
    get_user(db, user_id)
    item = user_query(db, FoodLog, user_id).filter(FoodLog.id == food_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food log not found")
    db.delete(item)
    db.commit()


@app.post("/foods/analyze", response_model=FoodAnalyzeOut)
def analyze_food(payload: FoodAnalyzeRequest) -> dict:
    analysis = enrich_food_log(payload.food_item, payload.meal_type, payload.notes)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Food AI analysis is unavailable.")
    return food_analysis_for_form(analysis)


@app.get("/foods", response_model=list[FoodLogOut])
def list_foods(user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> list[FoodLog]:
    return user_query(db, FoodLog, user_id).order_by(desc(FoodLog.entry_date)).limit(100).all()


@app.post("/finance-snapshots", response_model=FinanceSnapshotOut)
def create_finance_snapshot(
    payload: FinanceSnapshotCreate,
    user_id: int = Query(DEFAULT_USER_ID),
    db: Session = Depends(get_db),
) -> FinanceSnapshot:
    get_user(db, user_id)
    item = FinanceSnapshot(**with_user(payload.model_dump(), user_id))
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/finance-snapshots", response_model=list[FinanceSnapshotOut])
def list_finance_snapshots(user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> list[FinanceSnapshot]:
    return user_query(db, FinanceSnapshot, user_id).order_by(desc(FinanceSnapshot.entry_date)).limit(200).all()


@app.patch("/finance-snapshots/{snapshot_id}", response_model=FinanceSnapshotOut)
def update_finance_snapshot(
    snapshot_id: int,
    payload: FinanceSnapshotCreate,
    user_id: int = Query(DEFAULT_USER_ID),
    db: Session = Depends(get_db),
) -> FinanceSnapshot:
    item = get_owned_item(db, FinanceSnapshot, user_id, snapshot_id, "Finance snapshot")
    apply_payload(item, payload.model_dump())
    db.commit()
    db.refresh(item)
    return item


@app.delete("/finance-snapshots/{snapshot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_finance_snapshot(snapshot_id: int, user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> None:
    item = get_owned_item(db, FinanceSnapshot, user_id, snapshot_id, "Finance snapshot")
    db.delete(item)
    db.commit()


@app.post("/expenses", response_model=ExpenseLogOut)
def create_expense(payload: ExpenseLogCreate, user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> ExpenseLog:
    get_user(db, user_id)
    item = ExpenseLog(**with_user(payload.model_dump(), user_id))
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/expenses", response_model=list[ExpenseLogOut])
def list_expenses(user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> list[ExpenseLog]:
    return user_query(db, ExpenseLog, user_id).order_by(desc(ExpenseLog.expense_date), desc(ExpenseLog.expense_time)).limit(200).all()


@app.patch("/expenses/{expense_id}", response_model=ExpenseLogOut)
def update_expense(
    expense_id: int,
    payload: ExpenseLogCreate,
    user_id: int = Query(DEFAULT_USER_ID),
    db: Session = Depends(get_db),
) -> ExpenseLog:
    item = get_owned_item(db, ExpenseLog, user_id, expense_id, "Expense")
    apply_payload(item, payload.model_dump())
    db.commit()
    db.refresh(item)
    return item


@app.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> None:
    item = get_owned_item(db, ExpenseLog, user_id, expense_id, "Expense")
    db.delete(item)
    db.commit()


@app.post("/meds", response_model=MedLogOut)
def create_med(payload: MedLogCreate, user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> MedLog:
    get_user(db, user_id)
    item = MedLog(**with_user(payload.model_dump(), user_id))
    db.add(item)
    db.flush()
    sync_supplement_reminders(db, user_id)
    db.commit()
    db.refresh(item)
    return item


@app.get("/meds", response_model=list[MedLogOut])
def list_meds(user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> list[MedLog]:
    return user_query(db, MedLog, user_id).order_by(desc(MedLog.med_date), desc(MedLog.med_time)).limit(200).all()


@app.patch("/meds/{med_id}", response_model=MedLogOut)
def update_med(
    med_id: int,
    payload: MedLogCreate,
    user_id: int = Query(DEFAULT_USER_ID),
    db: Session = Depends(get_db),
) -> MedLog:
    item = get_owned_item(db, MedLog, user_id, med_id, "Med log")
    apply_payload(item, payload.model_dump())
    db.flush()
    sync_supplement_reminders(db, user_id)
    db.commit()
    db.refresh(item)
    return item


@app.delete("/meds/{med_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_med(med_id: int, user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> None:
    item = get_owned_item(db, MedLog, user_id, med_id, "Med log")
    db.delete(item)
    db.flush()
    sync_supplement_reminders(db, user_id)
    db.commit()


@app.post("/reminders", response_model=ReminderOut)
def create_reminder(payload: ReminderCreate, user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> Reminder:
    get_user(db, user_id)
    item = Reminder(**with_user(payload.model_dump(), user_id))
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/reminders", response_model=list[ReminderOut])
def list_reminders(user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> list[Reminder]:
    if db.query(UserProfile).filter(UserProfile.id == user_id).first():
        sync_supplement_reminders(db, user_id)
        db.commit()
    return user_query(db, Reminder, user_id).order_by(desc(Reminder.created_at)).limit(100).all()


@app.patch("/reminders/{reminder_id}", response_model=ReminderOut)
def update_reminder(
    reminder_id: int,
    payload: ReminderCreate,
    user_id: int = Query(DEFAULT_USER_ID),
    db: Session = Depends(get_db),
) -> Reminder:
    item = get_owned_item(db, Reminder, user_id, reminder_id, "Reminder")
    apply_payload(item, payload.model_dump())
    db.commit()
    db.refresh(item)
    return item


@app.delete("/reminders/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(reminder_id: int, user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> None:
    item = get_owned_item(db, Reminder, user_id, reminder_id, "Reminder")
    db.delete(item)
    db.commit()


@app.post("/challenges", response_model=ChallengeOut)
def create_challenge(payload: ChallengeCreate, user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> Challenge:
    get_user(db, user_id)
    existing = (
        user_query(db, Challenge, user_id)
        .filter(
            Challenge.title == payload.title,
            Challenge.start_date == payload.start_date,
            Challenge.end_date == payload.end_date,
            Challenge.target_weight_kg == payload.target_weight_kg,
        )
        .first()
    )
    if existing:
        return existing
    item = Challenge(**with_user(payload.model_dump(), user_id))
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/challenges", response_model=list[ChallengeOut])
def list_challenges(user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> list[Challenge]:
    return user_query(db, Challenge, user_id).order_by(desc(Challenge.start_date), desc(Challenge.created_at)).limit(50).all()


@app.patch("/challenges/{challenge_id}", response_model=ChallengeOut)
def update_challenge(
    challenge_id: int,
    payload: ChallengeCreate,
    user_id: int = Query(DEFAULT_USER_ID),
    db: Session = Depends(get_db),
) -> Challenge:
    item = get_owned_item(db, Challenge, user_id, challenge_id, "Challenge")
    apply_payload(item, payload.model_dump())
    db.commit()
    db.refresh(item)
    return item


@app.delete("/challenges/{challenge_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_challenge(challenge_id: int, user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> None:
    item = get_owned_item(db, Challenge, user_id, challenge_id, "Challenge")
    db.delete(item)
    db.commit()


@app.post("/trade-journal", response_model=TradeJournalEntryOut)
def create_trade_journal_entry(
    payload: TradeJournalEntryCreate, user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)
) -> TradeJournalEntry:
    get_user(db, user_id)
    item = TradeJournalEntry(**with_user(payload.model_dump(), user_id))
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/trade-journal", response_model=list[TradeJournalEntryOut])
def list_trade_journal_entries(user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> list[TradeJournalEntry]:
    return user_query(db, TradeJournalEntry, user_id).order_by(desc(TradeJournalEntry.entry_date), desc(TradeJournalEntry.created_at)).limit(200).all()


@app.patch("/trade-journal/{entry_id}", response_model=TradeJournalEntryOut)
def update_trade_journal_entry(
    entry_id: int,
    payload: TradeJournalEntryCreate,
    user_id: int = Query(DEFAULT_USER_ID),
    db: Session = Depends(get_db),
) -> TradeJournalEntry:
    item = get_owned_item(db, TradeJournalEntry, user_id, entry_id, "Trade journal entry")
    apply_payload(item, payload.model_dump())
    db.commit()
    db.refresh(item)
    return item


@app.delete("/trade-journal/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trade_journal_entry(entry_id: int, user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> None:
    item = get_owned_item(db, TradeJournalEntry, user_id, entry_id, "Trade journal entry")
    db.delete(item)
    db.commit()


@app.get("/trade-journal/insights", response_model=TradeLessonsInsightOut)
def get_trade_lessons_insight(user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> dict:
    entries = (
        user_query(db, TradeJournalEntry, user_id)
        .order_by(desc(TradeJournalEntry.entry_date))
        .limit(100)
        .all()
    )
    lessons = [entry.lessons_learnt.strip() for entry in entries if entry.lessons_learnt and entry.lessons_learnt.strip()]
    distilled = distill_trade_lessons(lessons)
    if distilled:
        return {"lessons": distilled, "source_count": len(lessons), "ai_generated": True}
    return {"lessons": lessons[:8], "source_count": len(lessons), "ai_generated": False}


@app.post("/todo-tasks", response_model=TodoTaskOut)
def create_todo_task(payload: TodoTaskCreate, user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> TodoTask:
    get_user(db, user_id)
    item = TodoTask(**with_user(payload.model_dump(), user_id))
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/todo-tasks", response_model=list[TodoTaskOut])
def list_todo_tasks(user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> list[TodoTask]:
    if db.query(UserProfile).filter(UserProfile.id == user_id).first():
        sync_recurring_tasks(db, user_id)
        db.commit()
    return user_query(db, TodoTask, user_id).order_by(TodoTask.task_due.is_(None), TodoTask.task_due, desc(TodoTask.created_at)).limit(500).all()


@app.patch("/todo-tasks/{task_id}", response_model=TodoTaskOut)
def update_todo_task(
    task_id: int,
    payload: TodoTaskCreate,
    user_id: int = Query(DEFAULT_USER_ID),
    db: Session = Depends(get_db),
) -> TodoTask:
    item = get_owned_item(db, TodoTask, user_id, task_id, "Task")
    apply_payload(item, payload.model_dump())
    db.commit()
    db.refresh(item)
    return item


@app.delete("/todo-tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo_task(task_id: int, user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> None:
    item = get_owned_item(db, TodoTask, user_id, task_id, "Task")
    db.delete(item)
    db.commit()


RECURRING_SCHEDULE_FIELDS = ("frequency", "day_of_week", "day_of_month", "month_of_year")


@app.post("/recurring-tasks", response_model=RecurringTaskOut)
def create_recurring_task(payload: RecurringTaskCreate, user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> RecurringTask:
    get_user(db, user_id)
    item = RecurringTask(**with_user(payload.model_dump(), user_id))
    item.task_due = compute_recurring_due_date(item.frequency, item.day_of_week, item.day_of_month, item.month_of_year, date.today())
    db.add(item)
    db.commit()
    db.refresh(item)
    sync_recurring_tasks(db, user_id)
    db.commit()
    db.refresh(item)
    return item


@app.get("/recurring-tasks", response_model=list[RecurringTaskOut])
def list_recurring_tasks(user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> list[RecurringTask]:
    return user_query(db, RecurringTask, user_id).order_by(desc(RecurringTask.created_at)).limit(200).all()


@app.patch("/recurring-tasks/{task_id}", response_model=RecurringTaskOut)
def update_recurring_task(
    task_id: int,
    payload: RecurringTaskCreate,
    user_id: int = Query(DEFAULT_USER_ID),
    db: Session = Depends(get_db),
) -> RecurringTask:
    item = get_owned_item(db, RecurringTask, user_id, task_id, "Recurring task")
    new_data = payload.model_dump()
    schedule_changed = any(getattr(item, field) != new_data.get(field) for field in RECURRING_SCHEDULE_FIELDS)
    apply_payload(item, new_data)
    if schedule_changed or item.task_due is None:
        item.task_due = compute_recurring_due_date(item.frequency, item.day_of_week, item.day_of_month, item.month_of_year, date.today())
    db.commit()
    db.refresh(item)
    sync_recurring_tasks(db, user_id)
    db.commit()
    db.refresh(item)
    return item


@app.delete("/recurring-tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recurring_task(task_id: int, user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> None:
    item = get_owned_item(db, RecurringTask, user_id, task_id, "Recurring task")
    db.delete(item)
    db.commit()


@app.get("/dashboard", response_model=DashboardOut)
def get_dashboard(user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> dict:
    profile = get_user(db, user_id)
    checkins = user_query(db, DailyCheckIn, user_id).order_by(desc(DailyCheckIn.entry_date)).limit(30).all()
    health = user_query(db, HealthMetric, user_id).order_by(desc(HealthMetric.entry_date)).limit(30).all()
    habits = user_query(db, HabitLog, user_id).order_by(desc(HabitLog.entry_date)).limit(200).all()
    foods = user_query(db, FoodLog, user_id).order_by(desc(FoodLog.entry_date)).limit(200).all()
    finance = user_query(db, FinanceSnapshot, user_id).order_by(desc(FinanceSnapshot.entry_date)).limit(500).all()

    category_scores = calculate_category_scores(checkins, health, habits, foods, finance)
    finance_summary = summarize_finance(finance)
    latest_health = health[0] if health else None
    latest_bp = None
    if latest_health and latest_health.systolic_bp and latest_health.diastolic_bp:
        latest_bp = f"{latest_health.systolic_bp}/{latest_health.diastolic_bp}"

    coach = build_coach_brief(category_scores, latest_health, checkins, foods, finance)

    return {
        "life_score": calculate_life_score(category_scores),
        "accountability_score": category_scores["accountability"],
        "category_scores": {key: value for key, value in category_scores.items() if key != "accountability"},
        "current_weight_kg": latest_health.weight_kg if latest_health and latest_health.weight_kg else profile.current_weight_kg if profile else None,
        "latest_bp": latest_bp,
        **finance_summary,
        "coach": coach,
    }


def build_challenge_reports(challenges: list[Challenge], health: list[HealthMetric]) -> list[dict]:
    reports: list[dict] = []
    for challenge in challenges:
        days: list[dict] = []
        current = challenge.start_date
        while current <= challenge.end_date:
            date_rows = [row for row in health if row.entry_date == current]
            weight_rows = [row for row in date_rows if row.weight_kg is not None]
            sugar_rows = [row for row in date_rows if row.blood_sugar is not None]
            latest_weight = max(weight_rows, key=health_sort_key) if weight_rows else None
            latest_sugar = max(sugar_rows, key=health_sort_key) if sugar_rows else None
            days.append(
                {
                    "entry_date": current,
                    "weight_kg": latest_weight.weight_kg if latest_weight else None,
                    "sugar": latest_sugar.blood_sugar if latest_sugar else None,
                    "sugar_context": latest_sugar.sugar_context if latest_sugar else None,
                    "sugar_time": latest_sugar.measurement_time if latest_sugar else None,
                }
            )
            current = current + timedelta(days=1)
        reports.append(
            {
                "id": challenge.id,
                "user_id": challenge.user_id,
                "title": challenge.title,
                "start_date": challenge.start_date,
                "end_date": challenge.end_date,
                "target_weight_kg": challenge.target_weight_kg,
                "notes": challenge.notes,
                "created_at": challenge.created_at,
                "days": days,
            }
        )
    return reports


def health_sort_key(row: HealthMetric) -> tuple:
    return (row.measurement_time is not None, row.measurement_time or datetime.min.time(), row.created_at)


def build_daily_reports(
    checkins: list[DailyCheckIn],
    health: list[HealthMetric],
    habits: list[HabitLog],
    foods: list[FoodLog],
    expenses: list[ExpenseLog],
    meds: list[MedLog],
    finance: list[FinanceSnapshot],
    reminders: list[Reminder],
) -> list[dict]:
    dates = {
        *[row.entry_date for row in checkins],
        *[row.entry_date for row in health],
        *[row.entry_date for row in habits],
        *[row.entry_date for row in foods],
        *[row.expense_date for row in expenses],
        *[row.med_date for row in meds],
        *[row.entry_date for row in finance],
        *[row.due_date for row in reminders if row.due_date],
    }
    reports: list[dict] = []
    for entry_date in sorted(dates, reverse=True):
        date_health = [row for row in health if row.entry_date == entry_date]
        weight_rows = [row for row in date_health if row.weight_kg is not None]
        bp_rows = [row for row in date_health if row.systolic_bp is not None and row.diastolic_bp is not None]
        sugar_rows = [row for row in date_health if row.blood_sugar is not None]
        body_rows = [
            row
            for row in date_health
            if any(
                value is not None
                for value in [row.body_fat_percent, row.muscle_percent, row.visceral_fat, row.body_age, row.bmr]
            )
        ]
        shite_rows = [row for row in date_health if row.shite_count is not None]
        latest_weight = max(weight_rows, key=health_sort_key) if weight_rows else None
        latest_bp = max(bp_rows, key=health_sort_key) if bp_rows else None
        latest_sugar = max(sugar_rows, key=health_sort_key) if sugar_rows else None
        latest_body = max(body_rows, key=health_sort_key) if body_rows else None
        latest_shite = max(shite_rows, key=health_sort_key) if shite_rows else None

        date_foods = [row for row in foods if row.entry_date == entry_date]
        quality_scores = [row.quality_score for row in date_foods if row.quality_score is not None]
        calories = [row.calories for row in date_foods if row.calories is not None]
        food_flags = sorted(
            {
                flag
                for row in date_foods
                for flag in [
                    "processed" if row.processed else None,
                    "direct sugar" if row.direct_sugar else None,
                    "refined" if row.refined else None,
                ]
                if flag
            }
        )

        date_habits = [row for row in habits if row.entry_date == entry_date]
        date_expenses = [row for row in expenses if row.expense_date == entry_date]
        date_meds = [row for row in meds if row.med_date == entry_date]
        date_finance = [row for row in finance if row.entry_date == entry_date]
        date_reminders = [row for row in reminders if row.due_date == entry_date]
        date_checkins = [row for row in checkins if row.entry_date == entry_date]
        journal_notes = [
            item
            for row in date_checkins
            for item in [
                f"Feeling: {row.feeling}" if row.feeling else None,
                f"Gratitude: {row.gratitude}" if row.gratitude else None,
                f"Journal: {row.journal_notes}" if row.journal_notes else None,
                row.notes,
            ]
            if item
        ]
        notes = [
            note
            for note in [
                *[row.notes for row in date_health],
                *[row.notes for row in date_foods],
                *[row.notes for row in date_habits],
                *[row.notes for row in date_expenses],
                *[row.notes for row in date_meds],
                *[row.notes for row in date_finance],
                *[row.notes for row in date_reminders],
                *journal_notes,
            ]
            if note
        ]

        reports.append(
            {
                "entry_date": entry_date,
                "weight_kg": latest_weight.weight_kg if latest_weight else None,
                "bp": f"{latest_bp.systolic_bp}/{latest_bp.diastolic_bp}" if latest_bp else None,
                "sugar": latest_sugar.blood_sugar if latest_sugar else None,
                "sugar_context": latest_sugar.sugar_context if latest_sugar else None,
                "sugar_time": latest_sugar.measurement_time if latest_sugar else None,
                "body_fat_percent": latest_body.body_fat_percent if latest_body else None,
                "muscle_percent": latest_body.muscle_percent if latest_body else None,
                "visceral_fat": latest_body.visceral_fat if latest_body else None,
                "body_age": latest_body.body_age if latest_body else None,
                "bmr": latest_body.bmr if latest_body else None,
                "shite_count": latest_shite.shite_count if latest_shite else None,
                "food_count": len(date_foods),
                "total_calories": sum(calories) if calories else None,
                "avg_quality_score": round(sum(quality_scores) / len(quality_scores), 1) if quality_scores else None,
                "food_items": [
                    f"{row.meal_type}: {row.food_item}"
                    + (f" ({row.calories:.0f} cal)" if row.calories is not None else "")
                    + (f", walk {row.post_meal_walk_meters:.0f} m" if row.post_meal_walk_meters else "")
                    for row in sorted(date_foods, key=lambda item: item.meal_time or datetime.min.time())
                ],
                "food_flags": food_flags,
                "habits_done": sum(1 for row in date_habits if row.completed),
                "habits_total": len(date_habits),
                "habit_items": [
                    (f"{row.habit_time} " if row.habit_time else "")
                    + f"{row.name}: {row.value if row.value is not None else '-'} {row.unit or ''}".strip()
                    + (" done" if row.completed else "")
                    for row in date_habits
                ],
                "med_items": [
                    (f"{row.med_time} " if row.med_time else "") + row.med_name
                    for row in sorted(date_meds, key=lambda item: item.med_time or datetime.min.time())
                ],
                "expense_items": [
                    f"{row.expense}: {row.cost:.0f} ({row.expense_type}, {row.expense_mode})"
                    for row in sorted(date_expenses, key=lambda item: item.expense_time or datetime.min.time())
                ],
                "total_expenses": sum(row.cost for row in date_expenses) if date_expenses else None,
                "finance_items": [
                    f"{row.kind}: {row.name} asset {row.value:.0f}, liability {row.liability_value:.0f}"
                    for row in date_finance
                ],
                "reminder_items": [
                    f"{row.title} ({row.category})" + (" done" if row.completed else "")
                    for row in date_reminders
                ],
                "notes": notes[:8],
            }
        )
    return reports[:90]


@app.get("/reports/{period}", response_model=ReportOut)
def get_report(period: str, user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> dict:
    get_user(db, user_id)
    checkins = user_query(db, DailyCheckIn, user_id).order_by(desc(DailyCheckIn.entry_date)).limit(90).all()
    health = user_query(db, HealthMetric, user_id).order_by(desc(HealthMetric.entry_date)).limit(90).all()
    habits = user_query(db, HabitLog, user_id).order_by(desc(HabitLog.entry_date)).limit(500).all()
    foods = user_query(db, FoodLog, user_id).order_by(desc(FoodLog.entry_date)).limit(500).all()
    expenses = user_query(db, ExpenseLog, user_id).order_by(desc(ExpenseLog.expense_date)).limit(500).all()
    meds = user_query(db, MedLog, user_id).order_by(desc(MedLog.med_date)).limit(500).all()
    finance = user_query(db, FinanceSnapshot, user_id).order_by(desc(FinanceSnapshot.entry_date)).limit(500).all()
    reminders = user_query(db, Reminder, user_id).order_by(desc(Reminder.created_at)).limit(500).all()
    challenges = user_query(db, Challenge, user_id).order_by(desc(Challenge.start_date), desc(Challenge.created_at)).limit(50).all()

    category_scores = calculate_category_scores(checkins, health, habits, foods, finance)
    finance_summary = summarize_finance(finance)
    latest_health = health[0] if health else None
    coach = build_coach_brief(category_scores, latest_health, checkins, foods, finance)

    trends: list[str] = []
    if len(health) >= 2 and health[0].weight_kg and health[-1].weight_kg:
        delta = health[0].weight_kg - health[-1].weight_kg
        trends.append(f"Weight change across available logs: {delta:+.1f} kg.")
    if foods:
        quality = sum((item.quality_score or 50) for item in foods) / len(foods)
        trends.append(f"Average food quality score: {quality:.0f}/100.")
        fasting_logs = [item for item in foods if item.fasting_type or item.fasting_hours]
        if fasting_logs:
            avg_fast = sum((item.fasting_hours or 0) for item in fasting_logs) / len(fasting_logs)
            trends.append(f"Fasting tracked {len(fasting_logs)} times; average fast: {avg_fast:.1f} hours.")
    if habits:
        completed = sum(1 for item in habits if item.completed)
        trends.append(f"Habit completion: {completed}/{len(habits)} logged items.")

    recommendations = coach["next_actions"][:]
    if not recommendations:
        recommendations.append("Keep logging daily and review one weak category this week.")

    return {
        "period": period,
        "life_score": calculate_life_score(category_scores),
        "accountability_score": category_scores["accountability"],
        "category_scores": {key: value for key, value in category_scores.items() if key != "accountability"},
        "trends": trends or ["Not enough data yet. Add logs for at least a few days."],
        "risks": coach["risks"],
        "recommendations": recommendations,
        "finance_summary": finance_summary,
        "challenges": build_challenge_reports(challenges, health),
        "daily_reports": build_daily_reports(checkins, health, habits, foods, expenses, meds, finance, reminders),
    }
