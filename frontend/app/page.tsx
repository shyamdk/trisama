"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  Dashboard,
  DailyCheckIn,
  DailyChecklistItem,
  DropdownOption,
  ExpenseLog,
  FoodAnalysis,
  FoodLog,
  HabitLog,
  HealthMetric,
  LoginResponse,
  MedLog,
  Reminder,
  Report,
  UserProfile,
  apiGet,
  apiGetAuth,
  apiDelete,
  apiDeleteAuth,
  apiPatch,
  apiPatchAuth,
  apiPost,
  apiPostAuth,
  userPath,
} from "@/lib/api";

const baseTabs = ["Dashboard", "Profile", "Journal", "Health", "Meds", "Food", "Exercise", "Sleep", "Career", "Bad Habits", "Expense Tracker", "Reminders", "Reports"];
const legacyFastingTimerStorageKey = "plos_fasting_countdown";
const legacyFastingTimerClearedKey = "plos_fasting_countdown_cleared_at";
const expiredFastingPromptMs = 12 * 60 * 60 * 1000;
const moduleOptions = [
  { key: "health", label: "Health" },
  { key: "meds", label: "Meds" },
  { key: "food", label: "Food" },
  { key: "exercise", label: "Exercise" },
  { key: "sleep", label: "Sleep" },
  { key: "career", label: "Career" },
  { key: "bad_habits", label: "Bad Habits" },
  { key: "expense_tracker", label: "Expense Tracker" },
  { key: "reminders", label: "Reminders" },
  { key: "journal", label: "Journal" },
];
const tabModule: Record<string, string | null> = {
  Dashboard: null,
  Profile: null,
  Journal: "journal",
  Health: "health",
  Meds: "meds",
  Food: "food",
  Exercise: "exercise",
  Sleep: "sleep",
  Career: "career",
  "Bad Habits": "bad_habits",
  "Expense Tracker": "expense_tracker",
  Reminders: "reminders",
  Reports: null,
  Admin: null,
};
const defaultDropdownOptions: Record<string, string[]> = {
  role: ["user", "admin"],
  coaching_tone: ["firm_practical", "gentle_supportive", "hard_accountability"],
  fasting_plan: ["16:8", "18:6", "Full day", "Custom"],
  sugar_context: ["Fasting", "PP", "Random"],
  meal_type: ["Breakfast", "Lunch", "Dinner", "Snack", "Fasting"],
  physical_exercise_name: ["Yoga", "Walking", "Cycling", "Strength Training"],
  mind_exercise_name: ["Meditation", "Pranayama"],
  spirit_exercise_name: ["Vishnu Sahasranamam"],
  sleep_name: ["Sleep Duration", "Sleep Quality", "Bed Time Consistency"],
  career_name: ["Job Application", "Interview", "Learning Session", "Networking"],
  bad_habit_name: ["Direct Sugar", "Processed Food", "Refined Food", "Smoking", "Alcohol", "Social Media"],
  expense_type: [
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
  expense_category: ["need", "want", "give"],
  expense_mode: ["UPI", "Credit Card", "Debit Card", "Cash", "Net Banking", "Wallet", "Auto Debit", "Cheque"],
  med_name: ["Tazloc CT 40"],
  reminder_category: ["health", "food", "exercise", "sleep", "insurance", "career"],
  reminder_channel: ["app", "telegram"],
};
const dropdownLabels: Record<string, string> = {
  role: "Role",
  coaching_tone: "Coaching tone",
  fasting_plan: "Fasting plan",
  sugar_context: "Sugar type",
  meal_type: "Meal type",
  physical_exercise_name: "Physical exercise item",
  mind_exercise_name: "Mind exercise item",
  spirit_exercise_name: "Spirit exercise item",
  sleep_name: "Sleep item",
  career_name: "Career item",
  bad_habit_name: "Bad habit item",
  expense_type: "Expense type",
  expense_category: "Expense category",
  expense_mode: "Expense mode",
  med_name: "Medicine",
  reminder_category: "Reminder category",
  reminder_channel: "Reminder channel",
};

type FastingCountdown = {
  userId: number;
  plan: string;
  mealType?: string | null;
  startAt: number;
  targetAt: number;
};

function numeric(form: FormData, key: string) {
  const value = form.get(key);
  if (value === null || value === "") return null;
  return Number(value);
}

function text(form: FormData, key: string) {
  const value = form.get(key);
  return value === null || value === "" ? null : String(value);
}

function setInputValue(form: HTMLFormElement, key: string, value: number | string | null) {
  const input = form.elements.namedItem(key);
  if (input instanceof HTMLInputElement && value !== null) {
    input.value = String(value);
  }
}

function setTextareaValue(form: HTMLFormElement, key: string, value: string) {
  const textarea = form.elements.namedItem(key);
  if (textarea instanceof HTMLTextAreaElement) {
    textarea.value = value;
  }
}

function setCheckboxValue(form: HTMLFormElement, key: string, checked: boolean) {
  const input = form.elements.namedItem(key);
  if (input instanceof HTMLInputElement) {
    input.checked = checked;
  }
}

function isoDate(offsetDays = 0) {
  const value = new Date();
  value.setDate(value.getDate() + offsetDays);
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function currentTime() {
  return new Date().toTimeString().slice(0, 5);
}

function timeValue(value?: string | null) {
  return value ? value.slice(0, 5) : null;
}

function sameLocalDate(left: Date, right: Date) {
  return left.getFullYear() === right.getFullYear() && left.getMonth() === right.getMonth() && left.getDate() === right.getDate();
}

function formatTimerEndTime(targetAt: number, now: number) {
  const target = new Date(targetAt);
  const today = new Date(now);
  const tomorrow = new Date(now);
  tomorrow.setDate(today.getDate() + 1);
  const time = target.toLocaleTimeString("en-IN", { hour: "numeric", minute: "2-digit", hour12: true });
  if (sameLocalDate(target, today)) return `Ends today at ${time}`;
  if (sameLocalDate(target, tomorrow)) return `Ends tomorrow at ${time}`;
  return `Ends ${target.toLocaleDateString("en-IN", { day: "numeric", month: "short" })} at ${time}`;
}

function fastingHours(plan?: string | null) {
  if (!plan) return 16;
  if (plan === "Full day") return 24;
  const match = plan.match(/^(\d+):/);
  return match ? Number(match[1]) : 16;
}

function mealGapHours(plan?: string | null) {
  if (plan === "18:6") return 3;
  if (plan === "16:8") return 4;
  return fastingHours(plan);
}

function timerDurationHoursForMeal(mealType: string | null | undefined, plan?: string | null) {
  if (!mealType || mealType === "Fasting" || mealType === "Drink") return null;
  if (mealType === "Dinner") return fastingHours(plan);
  return mealGapHours(plan);
}

function requiresPostMealWalk(mealType: string | null | undefined) {
  return mealType === "Breakfast" || mealType === "Lunch" || mealType === "Dinner";
}

function fastingTimerClearedKey(userId: number) {
  return `${legacyFastingTimerClearedKey}:${userId}`;
}

function removeLegacyFastingTimerStorage() {
  window.localStorage.removeItem(legacyFastingTimerStorageKey);
  window.localStorage.removeItem(legacyFastingTimerClearedKey);
}

function localTimestamp(entryDate: string | null, entryTime: string | null) {
  if (!entryDate) return Date.now();
  const time = entryTime || currentTime();
  const parsed = new Date(`${entryDate}T${time}`);
  return Number.isNaN(parsed.getTime()) ? Date.now() : parsed.getTime();
}

function fastingCountdownFromLatestMeal(foods: FoodLog[], plan: string, clearedAt: number, userId: number) {
  const now = Date.now();
  const mealRows = foods.filter((row) => {
    if (!row.meal_type || row.meal_type === "Fasting") return false;
    return localTimestamp(row.entry_date, row.meal_time) <= now + 2 * 60 * 1000;
  });
  if (!mealRows.length) return null;
  const latest = mealRows.reduce((current, row) => {
    const rowTime = localTimestamp(row.entry_date, row.meal_time);
    const currentTimeValue = localTimestamp(current.entry_date, current.meal_time);
    return rowTime > currentTimeValue ? row : current;
  });
  const startAt = localTimestamp(latest.entry_date, latest.meal_time);
  const durationHours = timerDurationHoursForMeal(latest.meal_type, plan);
  if (!durationHours) return null;
  const targetAt = startAt + durationHours * 60 * 60 * 1000;
  if (startAt <= clearedAt || targetAt <= Date.now() - expiredFastingPromptMs) return null;
  return { userId, plan, mealType: latest.meal_type, startAt, targetAt };
}

function enabledModules(user: UserProfile | null) {
  if (!user) return moduleOptions.map((item) => item.key);
  try {
    const parsed = JSON.parse(user.enabled_modules);
    return Array.isArray(parsed) ? parsed : moduleOptions.map((item) => item.key);
  } catch {
    return moduleOptions.map((item) => item.key);
  }
}

function dropdownValues(options: DropdownOption[], key: string) {
  const configured = options
    .filter((item) => item.dropdown_key === key)
    .sort((a, b) => a.sort_order - b.sort_order || a.label.localeCompare(b.label))
    .map((item) => item.value);
  return configured.length ? Array.from(new Set(configured)) : (defaultDropdownOptions[key] ?? []);
}

function dropdownGrouped(options: DropdownOption[]) {
  return Object.keys(dropdownLabels).map((key) => ({
    key,
    label: dropdownLabels[key],
    options: options
      .filter((item) => item.dropdown_key === key)
      .sort((a, b) => a.sort_order - b.sort_order || a.label.localeCompare(b.label)),
  }));
}

function isSessionError(error: unknown) {
  if (!(error instanceof Error)) return false;
  return ["Invalid or expired session", "Missing session token", "Session user not found"].some((message) => error.message.includes(message));
}

export default function Home() {
  const [active, setActive] = useState("Dashboard");
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [adminUsers, setAdminUsers] = useState<UserProfile[]>([]);
  const [authMode, setAuthMode] = useState<"login" | "forgot" | "reset">("login");
  const [resetToken, setResetToken] = useState("");
  const [authMessage, setAuthMessage] = useState("");
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [checkins, setCheckins] = useState<DailyCheckIn[]>([]);
  const [dailyChecklist, setDailyChecklist] = useState<DailyChecklistItem[]>([]);
  const [health, setHealth] = useState<HealthMetric[]>([]);
  const [meds, setMeds] = useState<MedLog[]>([]);
  const [habits, setHabits] = useState<HabitLog[]>([]);
  const [foods, setFoods] = useState<FoodLog[]>([]);
  const [expenses, setExpenses] = useState<ExpenseLog[]>([]);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [report, setReport] = useState<Report | null>(null);
  const [dropdownOptions, setDropdownOptions] = useState<DropdownOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [fastingCountdown, setFastingCountdown] = useState<FastingCountdown | null>(null);
  const [fastingTimerMode, setFastingTimerMode] = useState<"remaining" | "elapsed">("remaining");
  const [now, setNow] = useState(Date.now());

  const enabled = enabledModules(user);
  const tabs = (user?.role === "admin" ? [...baseTabs, "Admin"] : baseTabs).filter((tab) => {
    const module = tabModule[tab];
    return !module || enabled.includes(module);
  });

  const habitsByCategory = useMemo(() => {
    return habits.reduce<Record<string, HabitLog[]>>((acc, item) => {
      acc[item.category] = [...(acc[item.category] ?? []), item];
      return acc;
    }, {});
  }, [habits]);

  function resetUserScopedState() {
    setDashboard(null);
    setCheckins([]);
    setDailyChecklist([]);
    setHealth([]);
    setMeds([]);
    setHabits([]);
    setFoods([]);
    setExpenses([]);
    setReminders([]);
    setReport(null);
    setAdminUsers([]);
    setFastingCountdown(null);
    setFastingTimerMode("remaining");
  }

  async function loadAll(userOverride?: UserProfile, tokenOverride?: string) {
    const activeUser = userOverride ?? user;
    const activeToken = tokenOverride ?? token;
    if (!activeUser) return;
    setLoading(true);
    try {
      const currentUserId = activeUser.id;
      const [dash, checkinRows, checklistRows, healthRows, medRows, habitRows, foodRows, expenseRows, reminderRows, weeklyReport, userProfile, dropdownRows] = await Promise.all([
        apiGet<Dashboard>(userPath("/dashboard", currentUserId)),
        apiGet<DailyCheckIn[]>(userPath("/checkins", currentUserId)),
        apiGet<DailyChecklistItem[]>(userPath(`/daily-checklist?entry_date=${isoDate()}`, currentUserId)),
        apiGet<HealthMetric[]>(userPath("/health-metrics", currentUserId)),
        apiGet<MedLog[]>(userPath("/meds", currentUserId)),
        apiGet<HabitLog[]>(userPath("/habits", currentUserId)),
        apiGet<FoodLog[]>(userPath("/foods", currentUserId)),
        apiGet<ExpenseLog[]>(userPath("/expenses", currentUserId)),
        apiGet<Reminder[]>(userPath("/reminders", currentUserId)),
        apiGet<Report>(userPath("/reports/weekly", currentUserId)),
        apiGet<UserProfile>(`/users/${currentUserId}`),
        apiGet<DropdownOption[]>("/dropdown-options"),
      ]);
      setDashboard(dash);
      setCheckins(checkinRows);
      setDailyChecklist(checklistRows);
      setHealth(healthRows);
      setMeds(medRows);
      setHabits(habitRows);
      setFoods(foodRows);
      setExpenses(expenseRows);
      setReminders(reminderRows);
      setReport(weeklyReport);
      setUser(userProfile);
      setDropdownOptions(dropdownRows);
      if (userProfile.role === "admin" && activeToken) {
        try {
          setAdminUsers(await apiGetAuth<UserProfile[]>("/admin/users", activeToken));
        } catch (error) {
          if (isSessionError(error)) {
            expireSession();
            return;
          }
          throw error;
        }
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const storedToken = window.localStorage.getItem("plos_token");
    const storedUser = window.localStorage.getItem("plos_user");
    if (!storedToken || !storedUser) {
      setLoading(false);
      return;
    }
    const parsedUser = JSON.parse(storedUser) as UserProfile;
    setToken(storedToken);
    setUser(parsedUser);
    loadAll(parsedUser, storedToken);
  }, []);

  useEffect(() => {
    removeLegacyFastingTimerStorage();
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!user) return;
    if (!foods.length) {
      setFastingCountdown(null);
      return;
    }
    const clearedAt = Number(window.localStorage.getItem(fastingTimerClearedKey(user.id)) ?? 0);
    const derived = fastingCountdownFromLatestMeal(foods, user.fasting_plan ?? "16:8", clearedAt, user.id);
    if (!derived) {
      setFastingCountdown(null);
      return;
    }
    if (
      fastingCountdown &&
      fastingCountdown.userId === derived.userId &&
      fastingCountdown.startAt === derived.startAt &&
      fastingCountdown.targetAt === derived.targetAt
    ) {
      return;
    }
    setFastingCountdown(derived);
  }, [foods, user?.id, user?.fasting_plan, fastingCountdown]);

  function startFastingCountdown(entryDate: string | null, entryTime: string | null, mealType: string | null) {
    if (!user) return;
    const plan = user?.fasting_plan ?? "16:8";
    const durationHours = timerDurationHoursForMeal(mealType, plan);
    if (!durationHours) return;
    const startAt = localTimestamp(entryDate, entryTime);
    const nextCountdown = {
      userId: user.id,
      plan,
      mealType,
      startAt,
      targetAt: startAt + durationHours * 60 * 60 * 1000,
    };
    setFastingCountdown(nextCountdown);
    setFastingTimerMode("remaining");
    window.localStorage.removeItem(fastingTimerClearedKey(user.id));
  }

  function clearFastingCountdown() {
    setFastingCountdown(null);
    if (user) {
      window.localStorage.setItem(fastingTimerClearedKey(user.id), String(Date.now()));
    }
    removeLegacyFastingTimerStorage();
  }

  async function save(path: string, payload: unknown, form: HTMLFormElement) {
    setSaving(true);
    try {
      await apiPost(userPath(path, user?.id ?? 1), payload);
      form.reset();
      await loadAll();
    } finally {
      setSaving(false);
    }
  }

  async function submitJournal(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await save("/checkins", {
      entry_date: text(form, "entry_date"),
      feeling: text(form, "feeling"),
      mood: numeric(form, "mood"),
      energy: numeric(form, "energy"),
      stress: numeric(form, "stress"),
      day_rating: numeric(form, "day_rating"),
      gratitude: text(form, "gratitude"),
      journal_notes: text(form, "journal_notes"),
      notes: text(form, "notes"),
    }, event.currentTarget);
  }

  async function submitHealthMetric(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await save("/health-metrics", {
      entry_date: text(form, "entry_date"),
      measurement_time: text(form, "measurement_time"),
      weight_kg: numeric(form, "weight_kg"),
      systolic_bp: numeric(form, "systolic_bp"),
      diastolic_bp: numeric(form, "diastolic_bp"),
      blood_sugar: numeric(form, "blood_sugar"),
      sugar_context: text(form, "sugar_context"),
      body_fat_percent: numeric(form, "body_fat_percent"),
      muscle_percent: numeric(form, "muscle_percent"),
      visceral_fat: numeric(form, "visceral_fat"),
      body_age: numeric(form, "body_age"),
      bmr: numeric(form, "bmr"),
      shite_count: numeric(form, "shite_count"),
      notes: text(form, "notes"),
    }, event.currentTarget);
  }

  async function submitMed(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await save("/meds", {
      med_date: text(form, "med_date"),
      med_time: text(form, "med_time"),
      med_name: text(form, "med_name"),
      notes: text(form, "notes"),
    }, event.currentTarget);
  }

  async function submitHabit(event: FormEvent<HTMLFormElement>, categoryOverride?: string) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const completedValue = text(form, "completed");
    await save("/habits", {
      entry_date: text(form, "entry_date"),
      habit_time: text(form, "habit_time"),
      category: categoryOverride ?? text(form, "category"),
      name: text(form, "name"),
      value: numeric(form, "value"),
      unit: text(form, "unit"),
      target: numeric(form, "target"),
      completed: completedValue === "on" || completedValue === "true",
      notes: text(form, "notes"),
    }, event.currentTarget);
  }

  async function submitExpense(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await save("/expenses", {
      expense_date: text(form, "expense_date"),
      expense_time: text(form, "expense_time"),
      expense: text(form, "expense"),
      expense_type: text(form, "expense_type"),
      expense_category: text(form, "expense_category"),
      expense_mode: text(form, "expense_mode"),
      cost: numeric(form, "cost") ?? 0,
      notes: text(form, "notes"),
    }, event.currentTarget);
  }

  async function submitFood(event: FormEvent<HTMLFormElement>, foodId?: number) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const payload = {
      entry_date: text(form, "entry_date"),
      meal_time: text(form, "meal_time"),
      meal_type: text(form, "meal_type"),
      food_item: text(form, "food_item") ?? "",
      post_meal_walk_meters: numeric(form, "post_meal_walk_meters"),
      calories: numeric(form, "calories"),
      quality_score: numeric(form, "quality_score"),
      processed: form.get("processed") === "on",
      direct_sugar: form.get("direct_sugar") === "on",
      refined: form.get("refined") === "on",
      notes: text(form, "notes"),
    };
    const mealType = text(form, "meal_type");
    const entryDate = text(form, "entry_date");
    const entryTime = text(form, "meal_time");
    setSaving(true);
    try {
      if (foodId) {
        try {
          await apiPatch(userPath(`/foods/${foodId}`, user?.id ?? 1), payload);
        } catch (error) {
          if (error instanceof Error && error.message.includes("Food log not found")) {
            await loadAll();
            return;
          }
          throw error;
        }
      } else {
        await apiPost(userPath("/foods", user?.id ?? 1), payload);
      }
      formElement.reset();
      await loadAll();
      if (mealType) {
        startFastingCountdown(entryDate, entryTime, mealType);
      }
    } finally {
      setSaving(false);
    }
  }

  async function deleteFood(foodId: number) {
    if (!window.confirm("Delete this food log?")) return;
    setSaving(true);
    try {
      await apiDelete(userPath(`/foods/${foodId}`, user?.id ?? 1));
      await loadAll();
    } finally {
      setSaving(false);
    }
  }

  async function submitReminder(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await save("/reminders", {
      title: text(form, "title"),
      category: text(form, "category"),
      due_date: text(form, "due_date"),
      cadence: text(form, "cadence"),
      channel: text(form, "channel") ?? "app",
      completed: form.get("completed") === "on",
      notes: text(form, "notes"),
    }, event.currentTarget);
  }

  async function submitProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setSaving(true);
    try {
      if (!token || !user) return;
      await apiPatchAuth<UserProfile>(`/users/${user.id}`, {
        name: text(form, "name"),
        email: text(form, "email"),
        current_weight_kg: numeric(form, "current_weight_kg"),
        daily_calorie_target: numeric(form, "daily_calorie_target") ?? 1800,
        bp_medication: text(form, "bp_medication"),
        coaching_tone: text(form, "coaching_tone"),
        fasting_plan: text(form, "fasting_plan"),
        enabled_modules: JSON.stringify(form.getAll("enabled_modules").map(String)),
        notes: text(form, "notes"),
      }, token);
      await loadAll();
    } finally {
      setSaving(false);
    }
  }

  async function toggleDailyChecklistItem(item: DailyChecklistItem, completed: boolean) {
    if (!user) return;
    const updated = await apiPatch<DailyChecklistItem>(
      userPath(`/daily-checklist/${item.item_key}?entry_date=${item.entry_date}`, user.id),
      { completed },
    );
    setDailyChecklist((rows) => rows.map((row) => (row.id === updated.id ? updated : row)));
  }

  async function submitChangePassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;
    const form = new FormData(event.currentTarget);
    setSaving(true);
    try {
      const updated = await apiPostAuth<UserProfile>("/auth/change-password", {
        current_password: text(form, "current_password"),
        new_password: text(form, "new_password"),
      }, token);
      setUser(updated);
      window.localStorage.setItem("plos_user", JSON.stringify(updated));
      event.currentTarget.reset();
      await loadAll(updated, token);
    } finally {
      setSaving(false);
    }
  }

  async function submitLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setSaving(true);
    setAuthMessage("");
    try {
      const response = await apiPost<LoginResponse>("/auth/login", {
        email: text(form, "email"),
        password: text(form, "password"),
      });
      resetUserScopedState();
      removeLegacyFastingTimerStorage();
      setToken(response.token);
      setUser(response.user);
      window.localStorage.setItem("plos_token", response.token);
      window.localStorage.setItem("plos_user", JSON.stringify(response.user));
      await loadAll(response.user, response.token);
    } catch {
      setAuthMessage("Invalid email or password.");
    } finally {
      setSaving(false);
    }
  }

  function logout() {
    window.localStorage.removeItem("plos_token");
    window.localStorage.removeItem("plos_user");
    setToken(null);
    setUser(null);
    resetUserScopedState();
    removeLegacyFastingTimerStorage();
    setActive("Dashboard");
  }

  function expireSession() {
    logout();
    setAuthMode("login");
    setAuthMessage("Your admin session expired. Log in again, then retry the dropdown change.");
  }

  async function submitForgot(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setSaving(true);
    try {
      const response = await apiPost<{ message: string; reset_token: string | null }>("/auth/forgot-password", {
        email: text(form, "email"),
      });
      setResetToken(response.reset_token ?? "");
      setAuthMessage(response.reset_token ? `Reset token: ${response.reset_token}` : response.message);
      setAuthMode("reset");
    } finally {
      setSaving(false);
    }
  }

  async function submitReset(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setSaving(true);
    try {
      await apiPost("/auth/reset-password", {
        token: text(form, "token"),
        new_password: text(form, "new_password"),
      });
      setAuthMessage("Password reset. Log in with the new password.");
      setAuthMode("login");
    } finally {
      setSaving(false);
    }
  }

  if (!user) {
    return <AuthView mode={authMode} setMode={setAuthMode} resetToken={resetToken} message={authMessage} saving={saving} submitLogin={submitLogin} submitForgot={submitForgot} submitReset={submitReset} />;
  }

  return (
    <main className="page">
      <header className="topbar">
        <div>
          <div className="eyebrow">Personal Life Operating System</div>
          <h1>{active === "Dashboard" ? "North Star Dashboard" : active}</h1>
          <p className="muted">
            Manual Phase 1 app for {user?.name ?? "the default user"}.
            {user ? ` Current baseline: ${user.current_weight_kg} kg.` : ""}
          </p>
          <p className="muted">Logs can be entered for today or up to 2 days back.</p>
        </div>
        <div className="actions">
          <button className="button secondary" onClick={() => loadAll()} disabled={loading}>Refresh</button>
          <button className="button secondary" onClick={logout}>Logout</button>
        </div>
      </header>

      {fastingCountdown && (
        <GlobalFastingTimer
          countdown={fastingCountdown}
          mode={fastingTimerMode}
          now={now}
          flipMode={() => setFastingTimerMode(fastingTimerMode === "remaining" ? "elapsed" : "remaining")}
          clearCountdown={clearFastingCountdown}
        />
      )}

      <nav className="tabs">
        {tabs.map((tab) => (
          <button className={`tab ${active === tab ? "active" : ""}`} key={tab} onClick={() => setActive(tab)}>
            {tab}
          </button>
        ))}
      </nav>

      {active === "Dashboard" && dashboard && <DashboardView dashboard={dashboard} checklist={dailyChecklist} toggleChecklistItem={toggleDailyChecklistItem} />}
      {active === "Profile" && user && <ProfileView user={user} dropdownOptions={dropdownOptions} saving={saving} submitProfile={submitProfile} submitChangePassword={submitChangePassword} />}
      {active === "Journal" && <JournalView checkins={checkins} saving={saving} submitJournal={submitJournal} />}
      {active === "Health" && <HealthView health={health} dropdownOptions={dropdownOptions} saving={saving} submitHealthMetric={submitHealthMetric} />}
      {active === "Meds" && <MedsView meds={meds} dropdownOptions={dropdownOptions} saving={saving} submitMed={submitMed} />}
      {active === "Food" && <FoodView foods={foods} dropdownOptions={dropdownOptions} fastingPlan={user.fasting_plan ?? "16:8"} calorieTarget={user.daily_calorie_target ?? 1800} saving={saving} submitFood={submitFood} deleteFood={deleteFood} />}
      {active === "Exercise" && <ExerciseView rows={[...(habitsByCategory.exercise ?? []), ...(habitsByCategory.mind ?? [])]} dropdownOptions={dropdownOptions} saving={saving} submitHabit={submitHabit} />}
      {active === "Sleep" && <HabitView title="Sleep" category="sleep" rows={habitsByCategory.sleep ?? []} saving={saving} submitHabit={submitHabit} presets={dropdownValues(dropdownOptions, "sleep_name")} />}
      {active === "Career" && <HabitView title="Career & Growth" category="career" rows={[...(habitsByCategory.career ?? []), ...(habitsByCategory.growth ?? [])]} saving={saving} submitHabit={submitHabit} presets={dropdownValues(dropdownOptions, "career_name")} />}
      {active === "Bad Habits" && <HabitView title="Bad Habits" category="bad_habit" rows={habitsByCategory.bad_habit ?? []} saving={saving} submitHabit={submitHabit} presets={dropdownValues(dropdownOptions, "bad_habit_name")} />}
      {active === "Expense Tracker" && <ExpenseTrackerView expenses={expenses} dropdownOptions={dropdownOptions} saving={saving} submitExpense={submitExpense} />}
      {active === "Reminders" && <ReminderView reminders={reminders} dropdownOptions={dropdownOptions} saving={saving} submitReminder={submitReminder} />}
      {active === "Reports" && report && <ReportView report={report} userId={user.id} setReport={setReport} />}
      {active === "Admin" && user.role === "admin" && token && <AdminView users={adminUsers} dropdownOptions={dropdownOptions} token={token} saving={saving} setSaving={setSaving} reload={() => loadAll()} setDropdownOptions={setDropdownOptions} onAuthExpired={expireSession} />}
    </main>
  );
}

function AuthView({ mode, setMode, resetToken, message, saving, submitLogin, submitForgot, submitReset }: {
  mode: "login" | "forgot" | "reset";
  setMode: (mode: "login" | "forgot" | "reset") => void;
  resetToken: string;
  message: string;
  saving: boolean;
  submitLogin: (event: FormEvent<HTMLFormElement>) => void;
  submitForgot: (event: FormEvent<HTMLFormElement>) => void;
  submitReset: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <main className="page">
      <header className="topbar">
        <div>
          <div className="eyebrow">Personal Life Operating System</div>
          <h1>Login</h1>
        </div>
      </header>
      <section className="panel">
        {mode === "login" && (
          <form onSubmit={submitLogin}>
            <div className="form-grid">
              <label>Email<input name="email" type="email" autoComplete="username" required /></label>
              <label>Password<input name="password" type="password" autoComplete="current-password" required /></label>
            </div>
            {message && <p className="danger">{message}</p>}
            <div className="actions">
              <button className="button" disabled={saving}>Login</button>
              <button className="button secondary" type="button" onClick={() => setMode("forgot")}>Forgot Password</button>
            </div>
          </form>
        )}
        {mode === "forgot" && (
          <form onSubmit={submitForgot}>
            <label>Email<input name="email" type="email" required /></label>
            <div className="actions">
              <button className="button" disabled={saving}>Generate Reset Token</button>
              <button className="button secondary" type="button" onClick={() => setMode("login")}>Back</button>
            </div>
          </form>
        )}
        {mode === "reset" && (
          <form onSubmit={submitReset}>
            {message && <p className="muted">{message}</p>}
            <div className="form-grid">
              <label>Reset token<input name="token" defaultValue={resetToken} required /></label>
              <label>New password<input name="new_password" type="password" minLength={8} required /></label>
            </div>
            <div className="actions">
              <button className="button" disabled={saving}>Reset Password</button>
              <button className="button secondary" type="button" onClick={() => setMode("login")}>Back</button>
            </div>
          </form>
        )}
      </section>
    </main>
  );
}

function ProfileView({ user, dropdownOptions, saving, submitProfile, submitChangePassword }: { user: UserProfile; dropdownOptions: DropdownOption[]; saving: boolean; submitProfile: (event: FormEvent<HTMLFormElement>) => void; submitChangePassword: (event: FormEvent<HTMLFormElement>) => void }) {
  const enabled = enabledModules(user);
  const coachingToneOptions = dropdownValues(dropdownOptions, "coaching_tone");
  const fastingPlanOptions = dropdownValues(dropdownOptions, "fasting_plan");
  return (
    <div className="grid two">
      <Panel title="User Details">
        <div className="score-list section">
          <div className="score-row"><span>User ID</span><strong>{user.id}</strong></div>
          <div className="score-row"><span>Name</span><strong>{user.name}</strong></div>
          <div className="score-row"><span>Email</span><strong>{user.email}</strong></div>
          <div className="score-row"><span>Role</span><strong>{user.role}</strong></div>
          <div className="score-row"><span>Password change required</span><strong>{user.must_change_password ? "yes" : "no"}</strong></div>
          <div className="score-row"><span>Current weight</span><strong>{user.current_weight_kg} kg</strong></div>
          <div className="score-row"><span>Daily calorie target</span><strong>{user.daily_calorie_target ?? 1800} cal</strong></div>
          <div className="score-row"><span>BP medication</span><strong>{user.bp_medication}</strong></div>
          <div className="score-row"><span>Coaching tone</span><strong>{user.coaching_tone}</strong></div>
          <div className="score-row"><span>Fasting plan</span><strong>{user.fasting_plan}</strong></div>
        </div>
      </Panel>
      <Panel title="Edit User">
        <form className="section" onSubmit={submitProfile}>
          <div className="form-grid">
            <label>Name<input name="name" defaultValue={user.name} required /></label>
            <label>Email<input name="email" type="email" defaultValue={user.email ?? ""} required /></label>
            <label>Current weight kg<input name="current_weight_kg" type="number" step="0.1" defaultValue={user.current_weight_kg} required /></label>
            <label>Daily calorie target<input name="daily_calorie_target" type="number" step="1" defaultValue={user.daily_calorie_target ?? 1800} required /></label>
            <label>BP medication<input name="bp_medication" defaultValue={user.bp_medication} /></label>
            <label>Coaching tone<select name="coaching_tone" defaultValue={user.coaching_tone}>{coachingToneOptions.map((item) => <option key={item} value={item}>{item.replace("_", " ")}</option>)}</select></label>
            <label>Fasting plan<select name="fasting_plan" defaultValue={user.fasting_plan}>{fastingPlanOptions.map((item) => <option key={item}>{item}</option>)}</select></label>
          </div>
          <div className="section">
            <h3>Enabled Log Screens</h3>
            <div className="form-grid section">
              {moduleOptions.map((module) => (
                <label key={module.key}>
                  <span>
                    <input
                      name="enabled_modules"
                      type="checkbox"
                      value={module.key}
                      defaultChecked={enabled.includes(module.key)}
                    />{" "}
                    {module.label}
                  </span>
                </label>
              ))}
            </div>
          </div>
          <label>Notes<textarea name="notes" defaultValue={user.notes ?? ""} /></label>
          <button className="button" disabled={saving}>Save User Details</button>
        </form>
      </Panel>
      <Panel title="Change Password">
        <form className="section" onSubmit={submitChangePassword}>
          <div className="form-grid">
            <label>Current password<input name="current_password" type="password" required /></label>
            <label>New password<input name="new_password" type="password" minLength={8} required /></label>
          </div>
          <button className="button" disabled={saving}>Change Password</button>
        </form>
      </Panel>
    </div>
  );
}

function DashboardView({ dashboard, checklist, toggleChecklistItem }: { dashboard: Dashboard; checklist: DailyChecklistItem[]; toggleChecklistItem: (item: DailyChecklistItem, completed: boolean) => void }) {
  const completedItems = checklist.filter((item) => item.completed).length;
  return (
    <div className="stack">
      <section className="grid metrics">
        <Metric title="Life Score" value={String(dashboard.life_score)} note="0-1000 capped" />
        <Metric title="Accountability" value={String(dashboard.accountability_score)} note="Logging discipline" />
        <Metric title="Weight" value={`${dashboard.current_weight_kg ?? "-"} kg`} note="Latest logged" />
        <Metric title="BP" value={dashboard.latest_bp ?? "-"} note="Doctor supervision for medication" />
      </section>
      <Panel title="Today Logging Checklist">
        <div className="section">
          <div className="score-row"><span>{isoDate()}</span><strong>{completedItems}/{checklist.length} done</strong></div>
          <div className="checklist-grid section">
            {checklist.map((item) => (
              <label className="checklist-item" key={item.id}>
                <input type="checkbox" checked={item.completed} onChange={(event) => toggleChecklistItem(item, event.currentTarget.checked)} />
                <span>{item.label}</span>
              </label>
            ))}
          </div>
        </div>
      </Panel>
      <Panel title="Category Scores">
        <div className="score-list">{visibleCategoryScores(dashboard.category_scores).map(([key, value]) => <div className="score-row" key={key}><span>{key.replace("_", " ")}</span><strong>{value}</strong></div>)}</div>
      </Panel>
      <Panel title="AI Coach Brief">
        <div className="grid two section">
          <CoachList title="Wins" rows={dashboard.coach.wins} />
          <CoachList title="Risks" rows={dashboard.coach.risks} />
          <CoachList title="Missing Logs" rows={dashboard.coach.missing_logs} />
          <CoachList title="Next Actions" rows={dashboard.coach.next_actions} />
        </div>
      </Panel>
    </div>
  );
}

function JournalView({ checkins, saving, submitJournal }: { checkins: DailyCheckIn[]; saving: boolean; submitJournal: (event: FormEvent<HTMLFormElement>) => void }) {
  return (
    <div className="grid two">
      <Panel title="Journal Entry">
        <form className="section" onSubmit={submitJournal}>
          <div className="form-grid">
            <label>Entry date<input name="entry_date" type="date" defaultValue={isoDate()} min={isoDate(-2)} max={isoDate()} required /></label>
            <label>How I feel<input name="feeling" maxLength={120} /></label>
            <label>Mood<input name="mood" type="number" min="1" max="10" /></label>
            <label>Energy<input name="energy" type="number" min="1" max="10" /></label>
            <label>Stress<input name="stress" type="number" min="1" max="10" /></label>
            <label>Day rating<input name="day_rating" type="number" min="1" max="10" /></label>
          </div>
          <label>Gratitude<textarea name="gratitude" /></label>
          <label>Journal notes<textarea className="journal-textarea" name="journal_notes" /></label>
          <label>Notes<textarea name="notes" /></label>
          <button className="button" disabled={saving}>Save Journal</button>
        </form>
      </Panel>
      <Panel title="Recent Journal Entries"><JournalTable rows={checkins} /></Panel>
    </div>
  );
}

function HealthView({ health, dropdownOptions, saving, submitHealthMetric }: { health: HealthMetric[]; dropdownOptions: DropdownOption[]; saving: boolean; submitHealthMetric: (event: FormEvent<HTMLFormElement>) => void }) {
  const sugarContextOptions = dropdownValues(dropdownOptions, "sugar_context");
  return (
    <div className="grid two">
      <Panel title="BP Check-in">
        <form className="section" onSubmit={submitHealthMetric}>
          <div className="form-grid">
            <label>Entry date<input name="entry_date" type="date" defaultValue={isoDate()} min={isoDate(-2)} max={isoDate()} required /></label>
            <label>Time<input name="measurement_time" type="time" defaultValue={currentTime()} required /></label>
            <label>Systolic BP<input name="systolic_bp" type="number" /></label>
            <label>Diastolic BP<input name="diastolic_bp" type="number" /></label>
          </div>
          <label>Notes<textarea name="notes" /></label>
          <button className="button" disabled={saving}>Save BP</button>
        </form>
      </Panel>
      <Panel title="Sugar Check-in">
        <form className="section" onSubmit={submitHealthMetric}>
          <div className="form-grid">
            <label>Entry date<input name="entry_date" type="date" defaultValue={isoDate()} min={isoDate(-2)} max={isoDate()} required /></label>
            <label>Time<input name="measurement_time" type="time" defaultValue={currentTime()} required /></label>
            <label>Type<select name="sugar_context" defaultValue="Fasting">{sugarContextOptions.map((item) => <option key={item}>{item}</option>)}</select></label>
            <label>Blood sugar<input name="blood_sugar" type="number" step="0.1" /></label>
          </div>
          <label>Notes<textarea name="notes" /></label>
          <button className="button" disabled={saving}>Save Sugar</button>
        </form>
      </Panel>
      <Panel title="Body Metrics">
        <form className="section" onSubmit={submitHealthMetric}>
          <div className="form-grid">
            <label>Entry date<input name="entry_date" type="date" defaultValue={isoDate()} min={isoDate(-2)} max={isoDate()} required /></label>
            <label>Time<input name="measurement_time" type="time" defaultValue={currentTime()} /></label>
            <label>Weight kg<input name="weight_kg" type="number" step="0.1" /></label>
            <label>Body fat %<input name="body_fat_percent" type="number" step="0.1" /></label>
            <label>Muscle %<input name="muscle_percent" type="number" step="0.1" /></label>
            <label>Visceral fat<input name="visceral_fat" type="number" step="0.1" /></label>
            <label>Body age<input name="body_age" type="number" step="0.1" /></label>
            <label>BMR/RMR<input name="bmr" type="number" step="0.1" /></label>
          </div>
          <label>Notes<textarea name="notes" /></label>
          <button className="button" disabled={saving}>Save Body Metrics</button>
        </form>
      </Panel>
      <Panel title="Shite">
        <form className="section" onSubmit={submitHealthMetric}>
          <div className="form-grid">
            <label>Entry date<input name="entry_date" type="date" defaultValue={isoDate()} min={isoDate(-2)} max={isoDate()} required /></label>
            <label>Count<input name="shite_count" type="number" min="0" step="1" required /></label>
          </div>
          <label>Notes<textarea name="notes" /></label>
          <button className="button" disabled={saving}>Save Shite</button>
        </form>
      </Panel>
      <Panel title="Recent Health Logs"><HealthTable rows={health} /></Panel>
    </div>
  );
}

function MedsView({ meds, dropdownOptions, saving, submitMed }: { meds: MedLog[]; dropdownOptions: DropdownOption[]; saving: boolean; submitMed: (event: FormEvent<HTMLFormElement>) => void }) {
  const medOptions = dropdownValues(dropdownOptions, "med_name");
  return (
    <div className="grid two">
      <Panel title="Meds Entry">
        <form className="section" onSubmit={submitMed}>
          <div className="form-grid">
            <label>Date<input name="med_date" type="date" defaultValue={isoDate()} min={isoDate(-2)} max={isoDate()} required /></label>
            <label>Time<input name="med_time" type="time" defaultValue={currentTime()} required /></label>
            <label>Meds<select name="med_name" required>{medOptions.map((item) => <option key={item}>{item}</option>)}</select></label>
          </div>
          <label>Notes<textarea name="notes" /></label>
          <button className="button" disabled={saving}>Save Meds</button>
        </form>
      </Panel>
      <Panel title="Recent Meds"><MedTable rows={meds} /></Panel>
    </div>
  );
}

function FoodView({ foods, dropdownOptions, fastingPlan, calorieTarget, saving, submitFood, deleteFood }: { foods: FoodLog[]; dropdownOptions: DropdownOption[]; fastingPlan: string; calorieTarget: number; saving: boolean; submitFood: (event: FormEvent<HTMLFormElement>, foodId?: number) => Promise<void>; deleteFood: (foodId: number) => Promise<void> }) {
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState("");
  const [editingFood, setEditingFood] = useState<FoodLog | null>(null);
  const [selectedMealType, setSelectedMealType] = useState(editingFood?.meal_type ?? "Breakfast");
  const [postMealWalkMeters, setPostMealWalkMeters] = useState(editingFood?.post_meal_walk_meters === null || editingFood?.post_meal_walk_meters === undefined ? "" : String(editingFood.post_meal_walk_meters));
  const mealTypeOptions = dropdownValues(dropdownOptions, "meal_type");
  const calorieRows = useMemo(() => dailyCalorieRows(foods, calorieTarget), [foods, calorieTarget]);
  const fastingRows = useMemo(() => dailyFastingRows(foods), [foods]);
  const walkRequired = requiresPostMealWalk(selectedMealType);
  const walkDistanceReady = !walkRequired || Number(postMealWalkMeters) > 0;

  useEffect(() => {
    setSelectedMealType(editingFood?.meal_type ?? "Breakfast");
    setPostMealWalkMeters(editingFood?.post_meal_walk_meters === null || editingFood?.post_meal_walk_meters === undefined ? "" : String(editingFood.post_meal_walk_meters));
  }, [editingFood]);

  async function handleFoodSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (editingFood && !foods.some((food) => food.id === editingFood.id)) {
      setEditingFood(null);
      return;
    }
    try {
      await submitFood(event, editingFood?.id);
      setEditingFood(null);
      setSelectedMealType("Breakfast");
      setPostMealWalkMeters("");
    } catch (error) {
      if (error instanceof Error && error.message.includes("Food log not found")) {
        setEditingFood(null);
        return;
      }
      throw error;
    }
  }

  async function analyzeFood(form: HTMLFormElement) {
    const data = new FormData(form);
    const foodItem = text(data, "food_item");
    if (!foodItem) {
      setAnalyzeError("Enter food items before analyzing.");
      return;
    }
    if (requiresPostMealWalk(text(data, "meal_type")) && !(numeric(data, "post_meal_walk_meters") ?? 0)) {
      setAnalyzeError("Enter post-meal walk distance in meters before analyzing this meal.");
      return;
    }
    setAnalyzing(true);
    setAnalyzeError("");
    try {
      const result = await apiPost<FoodAnalysis>("/foods/analyze", {
        meal_type: text(data, "meal_type") ?? "",
        food_item: foodItem,
        notes: text(data, "notes"),
      });
      setInputValue(form, "calories", result.calories);
      setInputValue(form, "quality_score", result.quality_score);
      setTextareaValue(form, "notes", result.comments);
      setFoodFlagCheckboxes(form, result.ai_risk_flags);
    } catch (error) {
      setAnalyzeError(error instanceof Error ? error.message : "Food analysis failed. Check that the API server is running.");
    } finally {
      setAnalyzing(false);
    }
  }

  function cancelEdit() {
    setEditingFood(null);
  }

  async function handleDeleteFood(row: FoodLog) {
    await deleteFood(row.id);
    if (editingFood?.id === row.id) {
      setEditingFood(null);
    }
  }

  return (
    <div className="grid two">
      <Panel title="Food & Nutrition Log">
        <form className="section" key={editingFood?.id ?? "new-food"} onSubmit={handleFoodSubmit}>
          <div className="form-grid">
            <label>Entry date<input name="entry_date" type="date" defaultValue={editingFood?.entry_date ?? isoDate()} min={isoDate(-2)} max={isoDate()} required /></label>
            <label>Meal time<input name="meal_time" type="time" defaultValue={timeValue(editingFood?.meal_time) ?? currentTime()} /></label>
            <label>Meal type<select name="meal_type" value={selectedMealType} onChange={(event) => setSelectedMealType(event.currentTarget.value)} required>{mealTypeOptions.map((item) => <option key={item}>{item}</option>)}</select></label>
            <label className="wide-field">Food items<textarea className="compact-textarea" name="food_item" defaultValue={editingFood?.food_item ?? ""} placeholder="boiled egg (3), veges (100 gms)" /></label>
            <label>Post-meal walk distance (meters)<input name="post_meal_walk_meters" type="number" min="1" step="1" value={postMealWalkMeters} onChange={(event) => setPostMealWalkMeters(event.currentTarget.value)} required={walkRequired} /></label>
            <button className="button mini secondary" type="button" disabled={saving || analyzing || !walkDistanceReady} onClick={(event) => analyzeFood(event.currentTarget.form!)}>{analyzing ? "Analyzing..." : "Analyze"}</button>
            <label>Calories<input name="calories" type="number" step="0.1" defaultValue={editingFood?.calories ?? ""} /></label>
            <label>Quality score<input name="quality_score" type="number" min="0" max="100" defaultValue={editingFood?.quality_score ?? ""} /></label>
          </div>
          {walkRequired && !walkDistanceReady && <p className="muted">Post-meal walk distance in meters is required before analysis for breakfast, lunch, and dinner.</p>}
          {analyzeError && <p className="danger">{analyzeError}</p>}
          <div className="checkbox-group">
            <label className="checkbox-label"><input name="processed" type="checkbox" defaultChecked={editingFood?.processed ?? false} /> <span>Processed</span></label>
            <label className="checkbox-label"><input name="direct_sugar" type="checkbox" defaultChecked={editingFood?.direct_sugar ?? false} /> <span>Direct sugar</span></label>
            <label className="checkbox-label"><input name="refined" type="checkbox" defaultChecked={editingFood?.refined ?? false} /> <span>Refined</span></label>
          </div>
          <label>Comments<textarea name="notes" defaultValue={editingFood?.notes ?? ""} placeholder="AI comments on ingredients, quantity, quality, and risk flags can be updated here." /></label>
          <div className="actions">
            <button className="button" disabled={saving}>{editingFood ? "Update Food" : "Save Food"}</button>
            {editingFood && <button className="button secondary" type="button" onClick={cancelEdit}>Cancel Edit</button>}
          </div>
        </form>
      </Panel>
      <div className="stack">
        <Panel title="Daily Calories">
          <Table headers={["Date", "Consumed", "Target", "Balance", "Quality"]} rows={calorieRows.map((row) => [row.entryDate, `${row.consumed} cal`, `${row.target} cal`, row.balance >= 0 ? `${row.balance} cal left` : `${Math.abs(row.balance)} cal over`, row.quality === null ? "-" : `${row.quality}/100`])} />
        </Panel>
        <Panel title="Overnight Fasting">
          <Table headers={["Dinner Date", "Dinner", "Next Breakfast", "Fasted", "Target", "Balance"]} rows={fastingRows.map((row) => [row.dinnerDate, row.dinnerTime, `${row.breakfastDate} ${row.breakfastTime}`, row.fasted, "16h", row.balance])} />
        </Panel>
        <Panel title="Recent Food Logs"><FoodTable rows={foods} fastingPlan={fastingPlan} editFood={setEditingFood} deleteFood={handleDeleteFood} /></Panel>
      </div>
    </div>
  );
}

function GlobalFastingTimer({ countdown, mode, now, flipMode, clearCountdown }: { countdown: FastingCountdown; mode: "remaining" | "elapsed"; now: number; flipMode: () => void; clearCountdown: () => void }) {
  const remainingMs = Math.max(0, countdown.targetAt - now);
  const elapsedMs = Math.max(0, now - countdown.startAt);
  const overtimeMs = Math.max(0, now - countdown.targetAt);
  const valueMs = mode === "remaining" ? remainingMs : elapsedMs;
  const label = mode === "remaining" ? "remaining fast time" : "fasted so far";
  const isComplete = remainingMs <= 0;
  const timerName = countdown.mealType === "Dinner" ? "fasting timer" : "meal timer";
  const overtimeLabel = overtimeMs > 0 ? `+${formatDurationWords(overtimeMs)}` : null;

  return (
    <div className="global-timer">
      <div>
        <div className="eyebrow">{countdown.plan} {timerName}</div>
        <h2>
          {isComplete && mode === "remaining" ? "Fast complete" : `${formatDuration(valueMs)} ${label}`}
          {overtimeLabel && <span className="timer-overtime"> {overtimeLabel}</span>}
        </h2>
        <div className="timer-meta">{formatTimerEndTime(countdown.targetAt, now)}</div>
      </div>
      <div className="actions">
        <button className="button secondary" type="button" onClick={flipMode}>{mode === "remaining" ? "Show fasted" : "Show remaining"}</button>
        <button className="button secondary" type="button" onClick={clearCountdown}>Clear</button>
      </div>
    </div>
  );
}

function dailyCalorieRows(foods: FoodLog[], calorieTarget: number) {
  const grouped = foods.reduce<Record<string, { consumed: number; qualityScores: number[] }>>((acc, food) => {
    const row = acc[food.entry_date] ?? { consumed: 0, qualityScores: [] };
    row.consumed += food.calories ?? 0;
    if (food.quality_score !== null) row.qualityScores.push(food.quality_score);
    acc[food.entry_date] = row;
    return acc;
  }, {});

  return Object.entries(grouped)
    .sort(([left], [right]) => right.localeCompare(left))
    .slice(0, 14)
    .map(([entryDate, row]) => {
      const consumed = Math.round(row.consumed);
      return {
        entryDate,
        consumed,
        target: Math.round(calorieTarget),
        balance: Math.round(calorieTarget - consumed),
        quality: row.qualityScores.length ? Math.round(row.qualityScores.reduce((sum, value) => sum + value, 0) / row.qualityScores.length) : null,
      };
    });
}

function dailyFastingRows(foods: FoodLog[]) {
  const dinners = foods
    .filter((food) => food.meal_type === "Dinner" && food.meal_time)
    .sort((left, right) => right.entry_date.localeCompare(left.entry_date) || String(right.meal_time).localeCompare(String(left.meal_time)));
  const breakfasts = foods
    .filter((food) => food.meal_type === "Breakfast" && food.meal_time)
    .sort((left, right) => left.entry_date.localeCompare(right.entry_date) || String(left.meal_time).localeCompare(String(right.meal_time)));
  const targetMs = 16 * 60 * 60 * 1000;

  return dinners.slice(0, 14).flatMap((dinner) => {
    const dinnerAt = localTimestamp(dinner.entry_date, dinner.meal_time);
    const breakfast = breakfasts.find((candidate) => {
      const breakfastAt = localTimestamp(candidate.entry_date, candidate.meal_time);
      return breakfastAt > dinnerAt && candidate.entry_date > dinner.entry_date;
    });
    if (!breakfast) return [];
    const breakfastAt = localTimestamp(breakfast.entry_date, breakfast.meal_time);
    const fastedMs = breakfastAt - dinnerAt;
    const balanceMs = fastedMs - targetMs;
    return [{
      dinnerDate: dinner.entry_date,
      dinnerTime: timeValue(dinner.meal_time) ?? "-",
      breakfastDate: breakfast.entry_date,
      breakfastTime: timeValue(breakfast.meal_time) ?? "-",
      fasted: formatDurationShort(fastedMs),
      balance: balanceMs >= 0 ? `${formatDurationShort(balanceMs)} over` : `${formatDurationShort(Math.abs(balanceMs))} short`,
    }];
  });
}

function formatDurationShort(ms: number) {
  const totalMinutes = Math.max(0, Math.round(ms / 60000));
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  return minutes ? `${hours}h ${minutes}m` : `${hours}h`;
}

function formatDurationWords(ms: number) {
  const totalMinutes = Math.max(0, Math.floor(ms / 60000));
  if (totalMinutes < 1) return "<1min";
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  const parts = [];
  if (hours) parts.push(`${hours}hr${hours === 1 ? "" : "s"}`);
  if (minutes) parts.push(`${minutes}min${minutes === 1 ? "" : "s"}`);
  return parts.join(" ");
}

function formatDuration(ms: number) {
  const totalSeconds = Math.ceil(ms / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function ExerciseView({ rows, dropdownOptions, saving, submitHabit }: { rows: HabitLog[]; dropdownOptions: DropdownOption[]; saving: boolean; submitHabit: (event: FormEvent<HTMLFormElement>, category?: string) => void }) {
  return (
    <div className="grid two">
      <Panel title="Physical">
        <ExerciseEntryForm
          category="exercise"
          options={dropdownValues(dropdownOptions, "physical_exercise_name")}
          saving={saving}
          submitHabit={submitHabit}
        />
      </Panel>
      <Panel title="Mind and Spirits">
        <div className="stack section">
          <div>
            <h3>Mind</h3>
            <ExerciseEntryForm
              category="mind"
              options={dropdownValues(dropdownOptions, "mind_exercise_name")}
              saving={saving}
              submitHabit={submitHabit}
            />
          </div>
          <div>
            <h3>Spirit</h3>
            <ExerciseEntryForm
              category="mind"
              options={dropdownValues(dropdownOptions, "spirit_exercise_name")}
              saving={saving}
              submitHabit={submitHabit}
            />
          </div>
        </div>
      </Panel>
      <Panel title="Recent Exercise Logs"><HabitTable rows={rows} /></Panel>
    </div>
  );
}

function ExerciseEntryForm({ category, options, saving, submitHabit }: { category: string; options: string[]; saving: boolean; submitHabit: (event: FormEvent<HTMLFormElement>, category?: string) => void }) {
  return (
    <form className="section" onSubmit={(event) => submitHabit(event, category)}>
      <input name="unit" type="hidden" value="mins" />
      <input name="completed" type="hidden" value="true" />
      <div className="form-grid">
        <label>Item<select name="name" required>{options.map((item) => <option key={item}>{item}</option>)}</select></label>
        <label>Entry date<input name="entry_date" type="date" defaultValue={isoDate()} min={isoDate(-2)} max={isoDate()} required /></label>
        <label>Time<input name="habit_time" type="time" defaultValue={currentTime()} required /></label>
        <label>Mins<input name="value" type="number" min="1" step="1" required /></label>
      </div>
      <label>Notes<textarea name="notes" /></label>
      <button className="button" disabled={saving}>Save</button>
    </form>
  );
}

function HabitView({ title, category, rows, saving, submitHabit, presets }: { title: string; category: string; rows: HabitLog[]; saving: boolean; submitHabit: (event: FormEvent<HTMLFormElement>, category?: string) => void; presets: string[] }) {
  return (
    <div className="grid two">
      <Panel title={`${title} Log`}>
        <form className="section" onSubmit={(event) => submitHabit(event, category)}>
          <div className="form-grid">
            <label>Entry date<input name="entry_date" type="date" defaultValue={isoDate()} min={isoDate(-2)} max={isoDate()} required /></label>
            <label>Name<select name="name" required>{presets.map((item) => <option key={item}>{item}</option>)}</select></label>
            <label>Value<input name="value" type="number" step="0.1" /></label>
            <label>Unit<input name="unit" placeholder="mins, steps, km, count" /></label>
            <label>Target<input name="target" type="number" step="0.1" /></label>
          </div>
          <label className="checkbox-label"><input name="completed" type="checkbox" /> <span>Completed</span></label>
          <label>Notes<textarea name="notes" /></label>
          <button className="button" disabled={saving}>Save {title}</button>
        </form>
      </Panel>
      <Panel title={`Recent ${title} Logs`}><HabitTable rows={rows} /></Panel>
    </div>
  );
}

function ExpenseTrackerView({ expenses, dropdownOptions, saving, submitExpense }: { expenses: ExpenseLog[]; dropdownOptions: DropdownOption[]; saving: boolean; submitExpense: (event: FormEvent<HTMLFormElement>) => void }) {
  const expenseTypeOptions = dropdownValues(dropdownOptions, "expense_type");
  const expenseCategoryOptions = dropdownValues(dropdownOptions, "expense_category");
  const expenseModeOptions = dropdownValues(dropdownOptions, "expense_mode");
  const totalCost = expenses.reduce((sum, row) => sum + row.cost, 0);
  return (
    <div className="stack">
      <section className="grid metrics">
        <Metric title="Recent Spend" value={`Rs ${Math.round(totalCost)}`} note={`${expenses.length} logged expenses`} />
      </section>
      <div className="grid two">
        <Panel title="Expense Entry">
          <form className="section" onSubmit={submitExpense}>
            <div className="form-grid">
              <label>Expense<input name="expense" required /></label>
              <label>Expense date<input name="expense_date" type="date" defaultValue={isoDate()} required /></label>
              <label>Expense time<input name="expense_time" type="time" defaultValue={currentTime()} required /></label>
              <label>Expense type<select name="expense_type" required>{expenseTypeOptions.map((item) => <option key={item}>{item}</option>)}</select></label>
              <label>Expense cat<select name="expense_category" defaultValue="need" required>{expenseCategoryOptions.map((item) => <option key={item}>{item}</option>)}</select></label>
              <label>Expense mode<select name="expense_mode" defaultValue="UPI" required>{expenseModeOptions.map((item) => <option key={item}>{item}</option>)}</select></label>
              <label>Cost Rs.<input name="cost" type="number" min="0" step="0.01" required /></label>
            </div>
            <label>Notes<textarea name="notes" /></label>
            <button className="button" disabled={saving}>Save Expense</button>
          </form>
        </Panel>
        <Panel title="Recent Expenses"><ExpenseTable rows={expenses} /></Panel>
      </div>
    </div>
  );
}

function ReminderView({ reminders, dropdownOptions, saving, submitReminder }: { reminders: Reminder[]; dropdownOptions: DropdownOption[]; saving: boolean; submitReminder: (event: FormEvent<HTMLFormElement>) => void }) {
  const categoryOptions = dropdownValues(dropdownOptions, "reminder_category");
  const channelOptions = dropdownValues(dropdownOptions, "reminder_channel");
  return (
    <div className="grid two">
      <Panel title="Reminder Entry">
        <form className="section" onSubmit={submitReminder}>
          <div className="form-grid">
            <label>Title<input name="title" required /></label>
            <label>Category<select name="category" required>{categoryOptions.map((item) => <option key={item}>{item}</option>)}</select></label>
            <label>Due date<input name="due_date" type="date" /></label>
            <label>Cadence<input name="cadence" placeholder="daily, weekly, monthly" /></label>
            <label>Channel<select name="channel">{channelOptions.map((item) => <option key={item}>{item}</option>)}</select></label>
          </div>
          <label className="checkbox-label"><input name="completed" type="checkbox" /> <span>Completed</span></label>
          <label>Notes<textarea name="notes" /></label>
          <button className="button" disabled={saving}>Save Reminder</button>
        </form>
      </Panel>
      <Panel title="Reminder List"><ReminderTable rows={reminders} /></Panel>
    </div>
  );
}

function AdminView({ users, dropdownOptions, token, saving, setSaving, reload, setDropdownOptions, onAuthExpired }: {
  users: UserProfile[];
  dropdownOptions: DropdownOption[];
  token: string;
  saving: boolean;
  setSaving: (saving: boolean) => void;
  reload: () => Promise<void>;
  setDropdownOptions: (options: DropdownOption[]) => void;
  onAuthExpired: () => void;
}) {
  const [message, setMessage] = useState("");
  const [editingDropdown, setEditingDropdown] = useState<{ id: number; value: string; label: string } | null>(null);
  const roleOptions = dropdownValues(dropdownOptions, "role");
  const coachingToneOptions = dropdownValues(dropdownOptions, "coaching_tone");
  const fastingPlanOptions = dropdownValues(dropdownOptions, "fasting_plan");
  const groupedOptions = dropdownGrouped(dropdownOptions);

  async function submitCreateUser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setSaving(true);
    setMessage("");
    try {
      await apiPostAuth<UserProfile>("/admin/users", {
        name: text(form, "name"),
        email: text(form, "email"),
        role: text(form, "role"),
        default_password: text(form, "default_password"),
        current_weight_kg: numeric(form, "current_weight_kg") ?? 0,
        daily_calorie_target: numeric(form, "daily_calorie_target") ?? 1800,
        bp_medication: text(form, "bp_medication") ?? "",
        coaching_tone: text(form, "coaching_tone") ?? "firm_practical",
        fasting_plan: text(form, "fasting_plan") ?? "16:8",
        enabled_modules: JSON.stringify(moduleOptions.map((item) => item.key)),
        notes: text(form, "notes"),
      }, token);
      event.currentTarget.reset();
      setMessage("User created. Share the default password and ask them to change it after login.");
      await reload();
    } catch (error) {
      if (isSessionError(error)) {
        onAuthExpired();
        return;
      }
      setMessage(error instanceof Error ? error.message : "Could not create user.");
      await reload();
    } finally {
      setSaving(false);
    }
  }

  async function resetPassword(userId: number) {
    const newPassword = window.prompt("Temporary password");
    if (!newPassword) return;
    setSaving(true);
    setMessage("");
    try {
      await apiPostAuth(`/admin/users/${userId}/reset-password`, { new_password: newPassword }, token);
      setMessage("Password reset. Share the temporary password securely.");
      await reload();
    } catch (error) {
      if (isSessionError(error)) {
        onAuthExpired();
        return;
      }
      setMessage(error instanceof Error ? error.message : "Could not reset password.");
    } finally {
      setSaving(false);
    }
  }

  async function reloadDropdownOptions() {
    setDropdownOptions(await apiGet<DropdownOption[]>("/dropdown-options"));
  }

  async function submitDropdownOption(event: FormEvent<HTMLFormElement>, dropdownKeyOverride?: string) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    setSaving(true);
    setMessage("");
    try {
      await apiPostAuth<DropdownOption>("/admin/dropdown-options", {
        dropdown_key: dropdownKeyOverride ?? text(form, "dropdown_key"),
        value: text(form, "value"),
        label: text(form, "label"),
      }, token);
      formElement.reset();
      setMessage("Dropdown option saved.");
      await reloadDropdownOptions();
    } catch (error) {
      if (isSessionError(error)) {
        onAuthExpired();
        return;
      }
      setMessage(error instanceof Error ? error.message : "Could not save dropdown option.");
    } finally {
      setSaving(false);
    }
  }

  async function saveDropdownOption() {
    if (!editingDropdown) return;
    setSaving(true);
    setMessage("");
    try {
      await apiPatchAuth<DropdownOption>(`/admin/dropdown-options/${editingDropdown.id}`, {
        value: editingDropdown.value,
        label: editingDropdown.label,
      }, token);
      setEditingDropdown(null);
      setMessage("Dropdown option updated.");
      await reloadDropdownOptions();
    } catch (error) {
      if (isSessionError(error)) {
        onAuthExpired();
        return;
      }
      setMessage(error instanceof Error ? error.message : "Could not update dropdown option.");
    } finally {
      setSaving(false);
    }
  }

  async function deleteDropdownOption(optionId: number) {
    if (!window.confirm("Delete this dropdown option?")) return;
    setSaving(true);
    setMessage("");
    try {
      await apiDeleteAuth(`/admin/dropdown-options/${optionId}`, token);
      setMessage("Dropdown option deleted.");
      await reloadDropdownOptions();
    } catch (error) {
      if (isSessionError(error)) {
        onAuthExpired();
        return;
      }
      setMessage(error instanceof Error ? error.message : "Could not delete dropdown option.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="grid two">
      <Panel title="Create User">
        <form className="section" onSubmit={submitCreateUser}>
          <div className="form-grid">
            <label>Name<input name="name" required /></label>
            <label>Email<input name="email" type="email" required /></label>
            <label>Role<select name="role" defaultValue="user">{roleOptions.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
            <label>Temporary password<input name="default_password" type="password" autoComplete="new-password" minLength={8} required /></label>
            <label>Current weight kg<input name="current_weight_kg" type="number" step="0.1" defaultValue="0" /></label>
            <label>Daily calorie target<input name="daily_calorie_target" type="number" step="1" defaultValue="1800" /></label>
            <label>BP medication<input name="bp_medication" /></label>
            <label>Coaching tone<select name="coaching_tone" defaultValue="firm_practical">{coachingToneOptions.map((item) => <option key={item} value={item}>{item.replace("_", " ")}</option>)}</select></label>
            <label>Fasting plan<select name="fasting_plan" defaultValue="16:8">{fastingPlanOptions.map((item) => <option key={item}>{item}</option>)}</select></label>
          </div>
          <label>Notes<textarea name="notes" /></label>
          {message && <p className="muted">{message}</p>}
          <button className="button" disabled={saving}>Create User</button>
        </form>
      </Panel>
      <Panel title="Dropdown Options">
        {message && <p className="muted">{message}</p>}
        <form className="section" onSubmit={submitDropdownOption}>
          <div className="form-grid">
            <label>Dropdown<select name="dropdown_key" defaultValue="meal_type">{Object.entries(dropdownLabels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
            <label>Value<input name="value" required placeholder="Drink" /></label>
            <label>Label<input name="label" placeholder="Drink" /></label>
          </div>
          <button className="button" disabled={saving}>Add Dropdown Item</button>
        </form>
        <div className="stack section">
          {groupedOptions.map((group) => (
            <details className="challenge" key={group.key}>
              <summary>
                <strong>{group.label}</strong>
                <span>{group.options.length} items</span>
              </summary>
              <form className="section dropdown-add-form" onSubmit={(event) => submitDropdownOption(event, group.key)}>
                <div className="form-grid">
                  <label>Value<input name="value" required placeholder={`Add ${group.label.toLowerCase()}`} /></label>
                  <label>Label<input name="label" placeholder={`Add ${group.label.toLowerCase()}`} /></label>
                </div>
                <button className="button mini" disabled={saving}>Add {group.label}</button>
              </form>
              <div className="table-wrap section">
                <table>
                  <thead><tr><th>Value</th><th>Label</th><th>Action</th></tr></thead>
                  <tbody>
                    {group.options.map((item) => (
                      <tr key={item.id}>
                        {editingDropdown?.id === item.id ? (
                          <>
                            <td><input className="table-input" value={editingDropdown.value} onChange={(event) => setEditingDropdown({ ...editingDropdown, value: event.currentTarget.value })} /></td>
                            <td><input className="table-input" value={editingDropdown.label} onChange={(event) => setEditingDropdown({ ...editingDropdown, label: event.currentTarget.value })} /></td>
                            <td className="table-action"><button className="button mini" type="button" disabled={saving || !editingDropdown.value.trim()} onClick={saveDropdownOption}>Save</button><button className="button mini secondary" type="button" disabled={saving} onClick={() => setEditingDropdown(null)}>Cancel</button></td>
                          </>
                        ) : (
                          <>
                            <td>{item.value}</td>
                            <td>{item.label}</td>
                            <td className="table-action"><button className="button mini secondary" type="button" disabled={saving} onClick={() => setEditingDropdown({ id: item.id, value: item.value, label: item.label })}>Edit</button><button className="button mini secondary" type="button" disabled={saving} onClick={() => deleteDropdownOption(item.id)}>Delete</button></td>
                          </>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          ))}
        </div>
      </Panel>
      <Panel title="Users">
        <div className="table-wrap section">
          <table>
            <thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Role</th><th>Must Change</th><th>Action</th></tr></thead>
            <tbody>
              {users.map((item) => (
                <tr key={item.id}>
                  <td>{item.id}</td>
                  <td>{item.name}</td>
                  <td>{item.email}</td>
                  <td><span className="pill">{item.role}</span></td>
                  <td>{item.must_change_password ? "yes" : "no"}</td>
                  <td className="table-action"><button className="button secondary" onClick={() => resetPassword(item.id)} disabled={saving}>Reset Password</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}

function formatKg(value: number) {
  return `${Number.isInteger(value) ? value : value.toFixed(1)} kg`;
}

function challengeWeightSummary(challenge: Report["challenges"][number]) {
  const latestWeightDay = challenge.days
    .filter((day) => day.weight_kg !== null)
    .reduce<typeof challenge.days[number] | null>((latest, day) => {
      if (!latest) return day;
      return day.entry_date > latest.entry_date ? day : latest;
    }, null);

  if (!latestWeightDay?.weight_kg) {
    return { latest: "-", toGo: "-" };
  }

  const toGo = Math.max(0, latestWeightDay.weight_kg - challenge.target_weight_kg);
  return {
    latest: formatKg(latestWeightDay.weight_kg),
    toGo: formatKg(toGo),
  };
}

function listOrDash(items: string[]) {
  if (!items.length) return "-";
  return <ul className="compact-list">{items.map((item) => <li key={item}>{item}</li>)}</ul>;
}

function visibleCategoryScores(scores: Record<string, number>) {
  return Object.entries(scores).filter(([key]) => key !== "finance" && key !== "social");
}

function ReportView({ report, userId, setReport }: { report: Report; userId: number; setReport: (report: Report) => void }) {
  async function load(period: string) {
    setReport(await apiGet<Report>(userPath(`/reports/${period}`, userId)));
  }

  useEffect(() => {
    if (Array.isArray(report.daily_reports)) return;
    void load(report.period);
  }, [report.daily_reports, report.period, userId]);

  async function submitChallenge(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    await apiPost(userPath("/challenges", userId), {
      title: text(form, "title") ?? "21 Day Challenge",
      start_date: text(form, "start_date"),
      end_date: text(form, "end_date"),
      target_weight_kg: numeric(form, "target_weight_kg"),
      notes: text(form, "notes"),
    });
    formElement.reset();
    setReport(await apiGet<Report>(userPath(`/reports/${report.period}`, userId)));
  }
  async function deleteChallenge(challengeId: number) {
    if (!window.confirm("Delete this challenge?")) return;
    await apiDelete(userPath(`/challenges/${challengeId}`, userId));
    setReport(await apiGet<Report>(userPath(`/reports/${report.period}`, userId)));
  }
  return (
    <div className="stack">
      <div className="actions"><button className="button secondary" onClick={() => load("daily")}>Daily</button><button className="button secondary" onClick={() => load("weekly")}>Weekly</button><button className="button secondary" onClick={() => load("monthly")}>Monthly</button><button className="button secondary" onClick={() => load("quarterly")}>Quarterly</button></div>
      <section className="grid metrics"><Metric title="Period" value={report.period} note="Generated report" /><Metric title="Life Score" value={String(report.life_score)} note="0-1000" /><Metric title="Accountability" value={String(report.accountability_score)} note="Logging" /></section>
      <Panel title="Consolidated Daily Report">
        <div className="stack section">
          {report.daily_reports?.length ? report.daily_reports.map((day) => (
            <details className="challenge" key={day.entry_date}>
              <summary>
                <strong>{day.entry_date}</strong>
                <span>Weight: {day.weight_kg ?? "-"}</span>
                <span>BP: {day.bp ?? "-"}</span>
                <span>Sugar: {day.sugar ?? "-"}{day.sugar_context ? ` (${day.sugar_context})` : ""}</span>
                <span>Food: {day.food_count} / {day.total_calories ?? "-"} cal</span>
                <span>Habits: {day.habits_done}/{day.habits_total}</span>
              </summary>
              <Table
                headers={["Parameter", "Value"]}
                rows={[
                  ["Weight", day.weight_kg === null ? "-" : `${day.weight_kg} kg`],
                  ["BP", day.bp ?? "-"],
                  ["Sugar", day.sugar === null ? "-" : `${day.sugar}${day.sugar_context ? ` ${day.sugar_context}` : ""}${day.sugar_time ? ` at ${day.sugar_time}` : ""}`],
                  ["Body metrics", `Fat: ${day.body_fat_percent ?? "-"} | Muscle: ${day.muscle_percent ?? "-"} | Visceral: ${day.visceral_fat ?? "-"} | Body age: ${day.body_age ?? "-"} | BMR: ${day.bmr ?? "-"}`],
                  ["Shite", day.shite_count === null ? "-" : String(day.shite_count)],
                  ["Food", listOrDash(day.food_items)],
                  ["Food quality", `Avg score: ${day.avg_quality_score ?? "-"} | Flags: ${day.food_flags.length ? day.food_flags.join(", ") : "-"}`],
                  ["Habits", listOrDash(day.habit_items)],
                  ["Reminders", listOrDash(day.reminder_items)],
                  ["Notes", listOrDash(day.notes)],
                ]}
              />
            </details>
          )) : <p className="muted">No daily report data yet.</p>}
        </div>
      </Panel>
      <Panel title="21 Day Challenges">
        <form className="section" onSubmit={submitChallenge}>
          <div className="form-grid">
            <label>Title<input name="title" defaultValue="21 Day Challenge" /></label>
            <label>Target weight kg<input name="target_weight_kg" type="number" step="0.1" required /></label>
            <label>Start date<input name="start_date" type="date" defaultValue={isoDate()} required /></label>
            <label>End date<input name="end_date" type="date" defaultValue={isoDate(20)} required /></label>
          </div>
          <label>Notes<textarea name="notes" /></label>
          <button className="button">Create Challenge</button>
        </form>
        <div className="stack section">
          {report.challenges.length ? report.challenges.map((challenge) => {
            const weightSummary = challengeWeightSummary(challenge);
            return (
              <details className="challenge" key={challenge.id}>
                <summary>
                  <strong>{challenge.title}</strong>
                  <span>{challenge.start_date} to {challenge.end_date}</span>
                  <span>Target: {formatKg(challenge.target_weight_kg)}</span>
                  <span>Latest: {weightSummary.latest}</span>
                  <span>To go: {weightSummary.toGo}</span>
                  <button className="button mini secondary" type="button" onClick={(event) => { event.preventDefault(); deleteChallenge(challenge.id); }}>Delete</button>
                </summary>
                {challenge.notes && <p className="muted">{challenge.notes}</p>}
                <Table headers={["Date", "Weight", "Sugar", "Sugar Type", "Sugar Time"]} rows={challenge.days.map((day) => [day.entry_date, day.weight_kg ?? "-", day.sugar ?? "-", day.sugar_context ?? "-", day.sugar_time ?? "-"])} />
              </details>
            );
          }) : <p className="muted">No challenges yet.</p>}
        </div>
      </Panel>
      <section className="grid two"><Panel title="Trends"><CoachList title="" rows={report.trends} /></Panel><Panel title="Risks"><CoachList title="" rows={report.risks} /></Panel><Panel title="Recommendations"><CoachList title="" rows={report.recommendations} /></Panel><Panel title="Category Scores"><div className="score-list">{visibleCategoryScores(report.category_scores).map(([key, value]) => <div className="score-row" key={key}><span>{key.replace("_", " ")}</span><strong>{value}</strong></div>)}</div></Panel></section>
    </div>
  );
}

function Metric({ title, value, note }: { title: string; value: string; note: string }) {
  return <div className="card"><h3>{title}</h3><div className="metric-value">{value}</div><div className="muted">{note}</div></div>;
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="panel"><h2>{title}</h2>{children}</section>;
}

function CoachList({ title, rows }: { title: string; rows: string[] }) {
  return <div>{title && <h3>{title}</h3>}<ul className="coach-list">{rows.map((item) => <li key={item}>{item}</li>)}</ul></div>;
}

function JournalTable({ rows }: { rows: DailyCheckIn[] }) {
  return <Table headers={["Date", "Feeling", "Scores", "Gratitude", "Journal Notes"]} rows={rows.map((row) => [
    row.entry_date,
    row.feeling ?? "-",
    `Mood ${row.mood ?? "-"} | Energy ${row.energy ?? "-"} | Stress ${row.stress ?? "-"} | Day ${row.day_rating ?? "-"}`,
    row.gratitude ?? "-",
    row.journal_notes ?? row.notes ?? "-",
  ])} />;
}

function HealthTable({ rows }: { rows: HealthMetric[] }) {
  return <Table headers={["Date", "Time", "Weight", "BP", "Sugar", "Type", "Body Fat", "Shite", "Notes"]} rows={rows.map((row) => [row.entry_date, row.measurement_time ?? "-", row.weight_kg ?? "-", row.systolic_bp && row.diastolic_bp ? `${row.systolic_bp}/${row.diastolic_bp}` : "-", row.blood_sugar ?? "-", row.sugar_context ?? "-", row.body_fat_percent ?? "-", row.shite_count ?? "-", row.notes ?? "-"])} />;
}

function HabitTable({ rows }: { rows: HabitLog[] }) {
  return <Table headers={["Date", "Time", "Name", "Value", "Target", "Done", "Notes"]} rows={rows.map((row) => [row.entry_date, timeValue(row.habit_time) ?? "-", row.name, `${row.value ?? "-"} ${row.unit ?? ""}`, row.target ?? "-", row.completed ? "yes" : "no", row.notes ?? "-"])} />;
}

function FoodTable({ rows, fastingPlan, editFood, deleteFood }: { rows: FoodLog[]; fastingPlan: string; editFood: (row: FoodLog) => void; deleteFood: (row: FoodLog) => void }) {
  return <Table className="food-log-table" headers={["Edit", "Delete", "Date", "Time", "Meal", "Food", "Walk", "Fasting", "Est. grams", "Calories", "Macros", "Quality", "Flags"]} rows={rows.map((row) => [
    <button className="button mini secondary" type="button" onClick={() => editFood(row)}>Edit</button>,
    <button className="button mini danger" type="button" onClick={() => deleteFood(row)}>Delete</button>,
    row.entry_date,
    timeValue(row.meal_time) ?? "-",
    row.meal_type,
    row.food_item || "-",
    row.post_meal_walk_meters === null ? "-" : `${row.post_meal_walk_meters} m`,
    fastingPlan,
    row.quantity_grams ?? "-",
    row.calories ?? "-",
    `P:${row.protein ?? "-"} C:${row.carbs ?? "-"} F:${row.fat ?? "-"}`,
    row.quality_score ?? "-",
    foodFlags(row),
  ])} />;
}

function ExpenseTable({ rows }: { rows: ExpenseLog[] }) {
  return <Table headers={["Date", "Time", "Expense", "Type", "Cat", "Mode", "Cost", "Notes"]} rows={rows.map((row) => [
    row.expense_date,
    timeValue(row.expense_time) ?? "-",
    row.expense,
    row.expense_type,
    row.expense_category,
    row.expense_mode,
    `Rs ${row.cost}`,
    row.notes ?? "-",
  ])} />;
}

function MedTable({ rows }: { rows: MedLog[] }) {
  return <Table headers={["Date", "Time", "Meds", "Notes"]} rows={rows.map((row) => [
    row.med_date,
    timeValue(row.med_time) ?? "-",
    row.med_name,
    row.notes ?? "-",
  ])} />;
}

function setFoodFlagCheckboxes(form: HTMLFormElement, riskFlags: string[]) {
  const flags = new Set(riskFlags);
  setCheckboxValue(form, "direct_sugar", ["sweets", "fruit_juice", "sugary_tea_coffee"].some((flag) => flags.has(flag)));
  setCheckboxValue(form, "refined", ["simple_carbs", "rice", "chapati", "biscuits", "bakery_items"].some((flag) => flags.has(flag)));
  setCheckboxValue(form, "processed", ["biscuits", "sweets", "bakery_items", "chips", "fried_snacks"].some((flag) => flags.has(flag)));
}

function foodFlags(row: FoodLog) {
  const aiFlags = parseJsonList(row.ai_risk_flags);
  const manualFlags = [row.processed && "processed", row.direct_sugar && "sugar", row.refined && "refined"].filter(Boolean).map(String);
  const flags = aiFlags.length ? aiFlags : manualFlags;
  return flags.join(", ") || "-";
}

function parseJsonList(value: string | null) {
  if (!value) return [];
  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed.map(String) : [];
  } catch {
    return [];
  }
}

function ReminderTable({ rows }: { rows: Reminder[] }) {
  return <Table headers={["Title", "Category", "Due", "Cadence", "Channel", "Done"]} rows={rows.map((row) => [row.title, row.category, row.due_date ?? "-", row.cadence ?? "-", row.channel, row.completed ? "yes" : "no"])} />;
}

function Table({ headers, rows, className = "" }: { headers: string[]; rows: React.ReactNode[][]; className?: string }) {
  return (
    <div className="table-wrap section">
      <table className={className}>
        <thead><tr>{headers.map((header) => <th key={header}>{header}</th>)}</tr></thead>
        <tbody>
          {rows.length ? rows.map((row, index) => (
            <tr key={index}>
              {row.map((cell, cellIndex) => {
                const header = headers[cellIndex];
                const isAction = header === "Edit" || header === "Delete";
                return <td className={isAction ? "table-action" : undefined} data-label={header} key={cellIndex}>{cell}</td>;
              })}
            </tr>
          )) : <tr><td colSpan={headers.length}>No logs yet.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
