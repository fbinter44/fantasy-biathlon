const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    // Pydantic validation errors (422) retournent detail sous forme de tableau
    if (Array.isArray(err.detail)) {
      const msg = err.detail.map((e: { msg: string }) => e.msg).join(", ");
      throw new Error(msg);
    }
    throw new Error(err.detail ?? `Erreur ${res.status}`);
  }
  if (res.status === 204 || res.headers.get("content-length") === "0") {
    return undefined as T;
  }
  return res.json();
}

function authHeaders(token: string) {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

// --- Types ---

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  username: string;
}

export interface UserPublic {
  user_id: string;
  username: string;
  email: string;
}

export interface PlayerPoints {
  user_id: string;
  username: string;
  total_points: number;
  men_points: number;
  women_points: number;
  globe_points: number;
  rank: number;
}

export interface AthleteStanding {
  rank: number;
  ibu_id: string;
  name: string;
  nation: string;
  flag: string;
  points: number;
}

export interface DisciplineStandings {
  discipline: string;
  discipline_display: string;
  athletes: AthleteStanding[];
}

export interface StandingsResponse {
  gender: string;
  season_code: string;
  disciplines: DisciplineStandings[];
}

// --- Auth ---

export const auth = {
  login: (identifier: string, password: string) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identifier, password }),
    }),

  register: (username: string, email: string, password: string) =>
    request<UserPublic>("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password }),
    }),

  me: (token: string) =>
    request<UserPublic>("/auth/me", { headers: authHeaders(token) }),

  updateUsername: (new_username: string, token: string) =>
    request<UserPublic>("/auth/me/username", {
      method: "PATCH",
      headers: authHeaders(token),
      body: JSON.stringify({ new_username }),
    }),

  updatePassword: (old_password: string, new_password: string, token: string) =>
    request<{ detail: string }>("/auth/me/password", {
      method: "PATCH",
      headers: authHeaders(token),
      body: JSON.stringify({ old_password, new_password }),
    }),

  feedback: (feedback_type: string, subject: string, message: string, token: string) =>
    request<{ detail: string }>("/auth/feedback", {
      method: "POST",
      headers: authHeaders(token),
      body: JSON.stringify({ feedback_type, subject, message }),
    }),

  resetRequest: (email: string) =>
    request<{ detail: string }>("/auth/reset-request", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    }),

  resetPassword: (email: string, code: string, new_password: string) =>
    request<{ detail: string }>("/auth/reset-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, code, new_password }),
    }),
};

// --- Athletes ---

export interface AthleteResponse {
  ibu_id: string;
  family_name: string;
  given_name: string;
  nation: string;
  flag: string;
  gender: string;
  label: string;
}

export const athletes = {
  list: (gender?: "M" | "W") =>
    request<AthleteResponse[]>(`/athletes${gender ? `?gender=${gender}` : ""}`),
};

// --- Pronostics ---

export interface Top5 {
  p1: string; p2: string; p3: string; p4: string; p5: string;
}

export interface GlobeWinners {
  sprint_h: string; sprint_f: string;
  pursuit_h: string; pursuit_f: string;
  individual_h: string; individual_f: string;
  mass_start_h: string; mass_start_f: string;
}

export interface PronosticsResponse {
  user_id: string;
  username: string;
  top5_h: Top5;
  top5_f: Top5;
  globes: GlobeWinners;
}

export const pronostics = {
  me: (token: string) =>
    request<PronosticsResponse>("/pronostics/me", { headers: authHeaders(token) }),

  all: () =>
    request<PronosticsResponse[]>("/pronostics"),

  update: (body: { top5_h?: Top5; top5_f?: Top5; globes?: GlobeWinners }, token: string) =>
    request<PronosticsResponse>("/pronostics/me", {
      method: "PUT",
      headers: authHeaders(token),
      body: JSON.stringify(body),
    }),
};

// --- Leagues ---

export interface LeagueListItem {
  league_id: string;
  name: string;
  member_count: number;
  is_owner: boolean;
}

export interface LeagueMember {
  user_id: string;
  username: string;
}

export interface LeagueResponse {
  league_id: string;
  name: string;
  owner_id: string;
  invite_code: string;
  members: LeagueMember[];
}

export const leagues = {
  mine: (token: string) =>
    request<LeagueListItem[]>("/leagues", { headers: authHeaders(token) }),

  get: (league_id: string, token: string) =>
    request<LeagueResponse>(`/leagues/${league_id}`, { headers: authHeaders(token) }),

  create: (name: string, token: string) =>
    request<LeagueResponse>("/leagues", {
      method: "POST",
      headers: authHeaders(token),
      body: JSON.stringify({ name }),
    }),

  join: (invite_code: string, token: string) =>
    request<LeagueResponse>("/leagues/join", {
      method: "POST",
      headers: authHeaders(token),
      body: JSON.stringify({ invite_code }),
    }),

  delete: (league_id: string, token: string) =>
    request<void>(`/leagues/${league_id}`, {
      method: "DELETE",
      headers: authHeaders(token),
    }),

  leave: (league_id: string, token: string) =>
    request<void>(`/leagues/${league_id}/leave`, {
      method: "DELETE",
      headers: authHeaders(token),
    }),
};

// --- Classement ---

export interface VenueEvolution {
  index: number;
  name: string;
  start_date: string;
  end_date: string;
  players: PlayerPoints[];
}

export const classement = {
  global: () =>
    request<PlayerPoints[]>("/classement"),

  league: (league_id: string, token: string) =>
    request<PlayerPoints[]>(`/classement/league/${league_id}`, {
      headers: authHeaders(token),
    }),

  evolution: () =>
    request<VenueEvolution[]>("/classement/evolution"),
};

// --- Calendrier & Résultats ---

export interface RaceInfo {
  race_id: string;
  short_desc: string;
  discipline: string;
  discipline_display: string;
  gender: string;       // "Men" | "Women"
  start_time: string;   // ISO 8601
  is_past: boolean;
}

export interface VenueInfo {
  event_id: string;
  location: string;
  start_date: string;
  end_date: string;
  races: RaceInfo[];
}

export interface RaceResult {
  rank: number;
  name: string;
  ibu_id: string;
  nation: string;
  flag: string;
  points: number;
}

export const calendar = {
  venues: (token: string) =>
    request<VenueInfo[]>("/calendar", { headers: authHeaders(token) }),

  results: (race_id: string, token: string) =>
    request<RaceResult[]>(`/calendar/${race_id}/results`, { headers: authHeaders(token) }),
};

// --- Standings IBU ---

export interface SeasonProgress {
  discipline: string;
  races_done: number;
  races_total: number;
}

export const standings = {
  get: (gender: "Men" | "Women") =>
    request<StandingsResponse>(`/standings/${gender}`),

  progress: (gender: "Men" | "Women") =>
    request<SeasonProgress[]>(`/standings/${gender}/progress`),
};
