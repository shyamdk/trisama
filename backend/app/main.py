import hashlib
import os
import secrets
from datetime import date, datetime, timedelta
from typing import TypeVar

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine, get_db
from .food_ai import apply_food_enrichment, enrich_food_log, food_analysis_for_form
from .models import AuthSession, Challenge, DailyCheckIn, DailyChecklistItem, DropdownOption, FinanceSnapshot, FoodLog, HabitLog, HealthMetric, Reminder, UserProfile
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
    ReminderCreate,
    ReminderOut,
    ReportOut,
    ResetPasswordRequest,
    UserProfileOut,
    UserProfileUpdate,
)
from .scoring import build_coach_brief, calculate_category_scores, calculate_life_score, summarize_finance


app = FastAPI(title="PLOS API", version="0.1.0")
DEFAULT_USER_ID = 1
DEFAULT_ADMIN_EMAIL = os.getenv("PLOS_DEFAULT_ADMIN_EMAIL")
DEFAULT_ADMIN_PASSWORD = os.getenv("PLOS_DEFAULT_ADMIN_PASSWORD")
SESSION_DAYS = 7
DEFAULT_ENABLED_MODULES = '["health","food","exercise","sleep","social","career","bad_habits","finance","reminders"]'
UserOwnedModel = TypeVar("UserOwnedModel", DailyCheckIn, DailyChecklistItem, HealthMetric, HabitLog, FoodLog, FinanceSnapshot, Reminder, Challenge)
DEFAULT_DAILY_CHECKLIST = [
    ("body_metrics", "Weight / body metrics"),
    ("bp", "BP check-in"),
    ("sugar", "Sugar check-in"),
    ("food", "Food log"),
    ("exercise", "Exercise / movement"),
    ("sleep", "Sleep log"),
    ("bad_habits", "Bad habits check"),
]
DEFAULT_DROPDOWN_OPTIONS = {
    "role": ["user", "admin"],
    "coaching_tone": ["firm_practical", "gentle_supportive", "hard_accountability"],
    "fasting_plan": ["16:8", "18:6", "Full day", "Custom"],
    "sugar_context": ["Fasting", "PP", "Random"],
    "meal_type": ["Breakfast", "Lunch", "Dinner", "Snack", "Fasting"],
    "exercise_name": ["Walking", "Pranayama", "Meditation", "Yoga", "Strength Training", "Weekend Cardio"],
    "sleep_name": ["Sleep Duration", "Sleep Quality", "Bed Time Consistency"],
    "social_name": ["Call Friend", "Meet Friend/Cousin", "Bike Ride", "Comfort Zone Challenge"],
    "career_name": ["Job Application", "Interview", "Learning Session", "Networking"],
    "bad_habit_name": ["Direct Sugar", "Processed Food", "Refined Food", "Smoking", "Alcohol", "Social Media"],
    "finance_kind": ["property", "bank_account", "investment", "pf_retirement", "insurance", "liability", "expense", "trading"],
    "reminder_category": ["health", "food", "exercise", "sleep", "finance", "insurance", "social", "career"],
    "reminder_channel": ["app", "telegram"],
}

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
        ensure_dropdown_options(db)
        db.commit()


def ensure_user(db: Session) -> UserProfile:
    profile = db.query(UserProfile).filter(UserProfile.id == DEFAULT_USER_ID).first()
    if profile:
        profile.email = profile.email or DEFAULT_ADMIN_EMAIL
        profile.role = "admin"
        if not profile.password_hash and DEFAULT_ADMIN_PASSWORD:
            profile.password_hash = hash_password(DEFAULT_ADMIN_PASSWORD)
        profile.must_change_password = True if profile.must_change_password is None else profile.must_change_password
        profile.enabled_modules = profile.enabled_modules or DEFAULT_ENABLED_MODULES
        return profile
    profile = db.query(UserProfile).first()
    if profile:
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

    health_columns = {row[1] for row in db.connection().exec_driver_sql("PRAGMA table_info(health_metrics)")}
    if "measurement_time" not in health_columns:
        db.connection().exec_driver_sql("ALTER TABLE health_metrics ADD COLUMN measurement_time TIME")
    if "sugar_context" not in health_columns:
        db.connection().exec_driver_sql("ALTER TABLE health_metrics ADD COLUMN sugar_context VARCHAR(40)")


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
    for key, value in payload.model_dump(exclude_unset=True).items():
        if key == "role" and auth_user.role != "admin":
            continue
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
    return user_query(db, HabitLog, user_id).order_by(desc(HabitLog.entry_date)).limit(100).all()


@app.post("/foods", response_model=FoodLogOut)
def create_food(payload: FoodLogCreate, user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> FoodLog:
    get_user(db, user_id)
    food_payload = payload.model_dump()
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
    return user_query(db, Reminder, user_id).order_by(desc(Reminder.created_at)).limit(100).all()


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


@app.delete("/challenges/{challenge_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_challenge(challenge_id: int, user_id: int = Query(DEFAULT_USER_ID), db: Session = Depends(get_db)) -> None:
    get_user(db, user_id)
    item = user_query(db, Challenge, user_id).filter(Challenge.id == challenge_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")
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
    finance: list[FinanceSnapshot],
    reminders: list[Reminder],
) -> list[dict]:
    dates = {
        *[row.entry_date for row in checkins],
        *[row.entry_date for row in health],
        *[row.entry_date for row in habits],
        *[row.entry_date for row in foods],
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
        latest_weight = max(weight_rows, key=health_sort_key) if weight_rows else None
        latest_bp = max(bp_rows, key=health_sort_key) if bp_rows else None
        latest_sugar = max(sugar_rows, key=health_sort_key) if sugar_rows else None
        latest_body = max(body_rows, key=health_sort_key) if body_rows else None

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
        date_finance = [row for row in finance if row.entry_date == entry_date]
        date_reminders = [row for row in reminders if row.due_date == entry_date]
        date_checkins = [row for row in checkins if row.entry_date == entry_date]
        notes = [
            note
            for note in [
                *[row.notes for row in date_health],
                *[row.notes for row in date_foods],
                *[row.notes for row in date_habits],
                *[row.notes for row in date_finance],
                *[row.notes for row in date_reminders],
                *[row.notes for row in date_checkins],
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
                "food_count": len(date_foods),
                "total_calories": sum(calories) if calories else None,
                "avg_quality_score": round(sum(quality_scores) / len(quality_scores), 1) if quality_scores else None,
                "food_items": [
                    f"{row.meal_type}: {row.food_item}" + (f" ({row.calories:.0f} cal)" if row.calories is not None else "")
                    for row in sorted(date_foods, key=lambda item: item.meal_time or datetime.min.time())
                ],
                "food_flags": food_flags,
                "habits_done": sum(1 for row in date_habits if row.completed),
                "habits_total": len(date_habits),
                "habit_items": [
                    f"{row.name}: {row.value if row.value is not None else '-'} {row.unit or ''}".strip()
                    + (" done" if row.completed else "")
                    for row in date_habits
                ],
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
    if finance:
        trends.append(f"Current tracked net worth: Rs {finance_summary['net_worth']:.0f}.")
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
        "daily_reports": build_daily_reports(checkins, health, habits, foods, finance, reminders),
    }
