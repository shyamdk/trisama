const configuredApiBase = process.env.NEXT_PUBLIC_API_BASE;
export const DEFAULT_USER_ID = 1;

function apiBase() {
  if (configuredApiBase) return configuredApiBase;
  if (typeof window !== "undefined") {
    return `${window.location.protocol}//${window.location.hostname}:8010`;
  }
  return "http://127.0.0.1:8010";
}

export type UserProfile = {
  id: number;
  name: string;
  email: string | null;
  role: "admin" | "user" | string;
  must_change_password: boolean;
  current_weight_kg: number;
  daily_calorie_target: number;
  bp_medication: string;
  coaching_tone: string;
  fasting_plan: string;
  enabled_modules: string;
  notes: string | null;
};

export type LoginResponse = {
  token: string;
  user: UserProfile;
};

export type CoachBrief = {
  wins: string[];
  risks: string[];
  missing_logs: string[];
  next_actions: string[];
};

export type Dashboard = {
  life_score: number;
  accountability_score: number;
  category_scores: Record<string, number>;
  current_weight_kg: number | null;
  latest_bp: string | null;
  total_assets: number;
  total_liabilities: number;
  net_worth: number;
  liquid_assets: number;
  illiquid_assets: number;
  monthly_investments: number;
  monthly_expenses: number;
  coach: CoachBrief;
};

export type DailyChecklistItem = {
  id: number;
  user_id: number;
  entry_date: string;
  item_key: string;
  label: string;
  completed: boolean;
  created_at: string;
};

export type DailyCheckIn = {
  id: number;
  user_id: number;
  entry_date: string;
  feeling: string | null;
  mood: number | null;
  energy: number | null;
  stress: number | null;
  day_rating: number | null;
  gratitude: string | null;
  journal_notes: string | null;
  notes: string | null;
  created_at: string;
};

export type HealthMetric = {
  id: number;
  entry_date: string;
  measurement_time: string | null;
  weight_kg: number | null;
  systolic_bp: number | null;
  diastolic_bp: number | null;
  blood_sugar: number | null;
  sugar_context: string | null;
  body_fat_percent: number | null;
  muscle_percent: number | null;
  visceral_fat: number | null;
  body_age: number | null;
  bmr: number | null;
  shite_count: number | null;
  notes: string | null;
};

export type HabitLog = {
  id: number;
  entry_date: string;
  habit_time: string | null;
  category: string;
  name: string;
  value: number | null;
  unit: string | null;
  target: number | null;
  completed: boolean;
  notes: string | null;
};

export type FoodLog = {
  id: number;
  entry_date: string;
  meal_time: string | null;
  meal_type: string;
  food_item: string;
  post_meal_walk_meters: number | null;
  fasting_type: string | null;
  fasting_hours: number | null;
  eating_window_hours: number | null;
  quantity_grams: number | null;
  calories: number | null;
  protein: number | null;
  carbs: number | null;
  fat: number | null;
  fibre: number | null;
  quality_score: number | null;
  processed: boolean;
  direct_sugar: boolean;
  refined: boolean;
  ai_enriched: boolean;
  ai_ingredients: string | null;
  ai_risk_flags: string | null;
  ai_notes: string | null;
  notes: string | null;
};

export type FoodAnalysis = {
  quantity_grams: number | null;
  calories: number | null;
  protein: number | null;
  carbs: number | null;
  fat: number | null;
  fibre: number | null;
  quality_score: number | null;
  comments: string;
  ai_risk_flags: string[];
  ai_ingredients: Record<string, unknown>[];
};

export type FinanceSnapshot = {
  id: number;
  entry_date: string;
  kind: string;
  name: string;
  value: number;
  liability_value: number;
  monthly_cashflow: number | null;
  renewal_date: string | null;
  notes: string | null;
};

export type ExpenseLog = {
  id: number;
  user_id: number;
  expense_date: string;
  expense_time: string | null;
  expense: string;
  expense_type: string;
  expense_category: string;
  expense_mode: string;
  cost: number;
  notes: string | null;
  created_at: string;
};

export type MedLog = {
  id: number;
  user_id: number;
  med_date: string;
  med_time: string | null;
  med_name: string;
  notes: string | null;
  created_at: string;
};

export type Reminder = {
  id: number;
  title: string;
  category: string;
  due_date: string | null;
  cadence: string | null;
  channel: string;
  completed: boolean;
  notes: string | null;
};

export type DropdownOption = {
  id: number;
  dropdown_key: string;
  value: string;
  label: string;
  sort_order: number;
  created_at: string;
};

export type Report = {
  period: string;
  life_score: number;
  accountability_score: number;
  category_scores: Record<string, number>;
  trends: string[];
  risks: string[];
  recommendations: string[];
  finance_summary: Record<string, number>;
  challenges: ChallengeReport[];
  daily_reports: DailyConsolidatedReport[];
};

export type DailyConsolidatedReport = {
  entry_date: string;
  weight_kg: number | null;
  bp: string | null;
  sugar: number | null;
  sugar_context: string | null;
  sugar_time: string | null;
  body_fat_percent: number | null;
  muscle_percent: number | null;
  visceral_fat: number | null;
  body_age: number | null;
  bmr: number | null;
  shite_count: number | null;
  food_count: number;
  total_calories: number | null;
  avg_quality_score: number | null;
  food_items: string[];
  food_flags: string[];
  habits_done: number;
  habits_total: number;
  habit_items: string[];
  med_items: string[];
  expense_items: string[];
  total_expenses: number | null;
  finance_items: string[];
  reminder_items: string[];
  notes: string[];
};

export type ChallengeReport = {
  id: number;
  title: string;
  start_date: string;
  end_date: string;
  target_weight_kg: number;
  notes: string | null;
  created_at: string;
  days: ChallengeDay[];
};

export type ChallengeDay = {
  entry_date: string;
  weight_kg: number | null;
  sugar: number | null;
  sugar_context: string | null;
  sugar_time: string | null;
};

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBase()}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }
  return response.json();
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${apiBase()}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }
  return response.json();
}

export async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${apiBase()}${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }
  return response.json();
}

export async function apiDelete(path: string): Promise<void> {
  const response = await fetch(`${apiBase()}${path}`, { method: "DELETE" });
  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }
}

export async function apiDeleteAuth(path: string, token: string): Promise<void> {
  const response = await fetch(`${apiBase()}${path}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }
}

export async function apiGetAuth<T>(path: string, token: string): Promise<T> {
  const response = await fetch(`${apiBase()}${path}`, {
    cache: "no-store",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }
  return response.json();
}

export async function apiPostAuth<T>(path: string, body: unknown, token: string): Promise<T> {
  const response = await fetch(`${apiBase()}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }
  return response.json();
}

export async function apiPatchAuth<T>(path: string, body: unknown, token: string): Promise<T> {
  const response = await fetch(`${apiBase()}${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }
  return response.json();
}

export function userPath(path: string, userId: number = DEFAULT_USER_ID) {
  const separator = path.includes("?") ? "&" : "?";
  return `${path}${separator}user_id=${userId}`;
}

async function errorMessage(response: Response) {
  try {
    const payload = await response.json();
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
    if (Array.isArray(payload.detail)) {
      return payload.detail.map((item: { msg?: string }) => item.msg ?? JSON.stringify(item)).join(", ");
    }
  } catch {
    // Fall through to generic status message.
  }
  return `API request failed: ${response.status}`;
}
