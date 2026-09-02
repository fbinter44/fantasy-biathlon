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
  race_points: number;
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
  me: (token: string, season?: string) =>
    request<PronosticsResponse>(`/pronostics/me${season ? `?season=${season}` : ""}`, { headers: authHeaders(token) }),

  all: (season?: string) =>
    request<PronosticsResponse[]>(`/pronostics${season ? `?season=${season}` : ""}`),

  update: (body: { top5_h?: Top5; top5_f?: Top5; globes?: GlobeWinners }, token: string, season?: string) =>
    request<PronosticsResponse>(`/pronostics/me${season ? `?season=${season}` : ""}`, {
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

// --- Score breakdown ---

export interface AthleteScoreDetail {
  predicted_rank: number;
  ibu_id: string;
  name: string;
  nation: string;
  actual_rank: number | null;
  points: number;
  exact_rank_bonus: boolean;
}

export interface GlobeScoreDetail {
  discipline: string;
  discipline_display: string;
  gender: string;
  predicted_ibu_id: string;
  predicted_name: string;
  actual_leader_ibu_id: string | null;
  actual_leader_name: string | null;
  points: number;
  correct: boolean;
}

export interface RaceScoreDetail {
  race_id: string;
  location: string;
  discipline_display: string;
  gender: string;
  date: string;
  predicted_ibu_id: string;
  predicted_name: string;
  winner_ibu_id: string | null;
  winner_name: string | null;
  points: number;
  correct: boolean;
}

export interface ScoreBreakdown {
  user_id: string;
  username: string;
  total_points: number;
  men_points: number;
  women_points: number;
  globe_points: number;
  race_points: number;
  men_athletes: AthleteScoreDetail[];
  women_athletes: AthleteScoreDetail[];
  globes: GlobeScoreDetail[];
  races: RaceScoreDetail[];
}

export const score = {
  get: (user_id: string, token: string, season?: string) =>
    request<ScoreBreakdown>(`/score/${user_id}${season ? `?season=${season}` : ""}`, { headers: authHeaders(token) }),
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
  global: (season?: string) =>
    request<PlayerPoints[]>(`/classement${season ? `?season=${season}` : ""}`),

  league: (league_id: string, token: string, season?: string) =>
    request<PlayerPoints[]>(`/classement/league/${league_id}${season ? `?season=${season}` : ""}`, {
      headers: authHeaders(token),
    }),

  evolution: (season?: string) =>
    request<VenueEvolution[]>(`/classement/evolution${season ? `?season=${season}` : ""}`),
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
  venues: (token: string, season?: string) =>
    request<VenueInfo[]>(`/calendar${season ? `?season=${season}` : ""}`, { headers: authHeaders(token) }),

  results: (race_id: string, token: string, season?: string) =>
    request<RaceResult[]>(`/calendar/${race_id}/results${season ? `?season=${season}` : ""}`, { headers: authHeaders(token) }),
};

// --- Race pronostics ---

export interface RacePronosticsResponse {
  pronos: Record<string, string>; // {race_id: ibu_id}
}

export const racePronostics = {
  get: (token: string, season?: string) =>
    request<RacePronosticsResponse>(`/race-pronostics${season ? `?season=${season}` : ""}`, { headers: authHeaders(token) }),

  set: (race_id: string, ibu_id: string, token: string, season?: string) =>
    request<RacePronosticsResponse>(`/race-pronostics/${race_id}${season ? `?season=${season}` : ""}`, {
      method: "PUT",
      headers: authHeaders(token),
      body: JSON.stringify({ ibu_id }),
    }),

  remove: (race_id: string, token: string, season?: string) =>
    request<void>(`/race-pronostics/${race_id}${season ? `?season=${season}` : ""}`, {
      method: "DELETE",
      headers: authHeaders(token),
    }),
};

// --- Standings IBU ---

export interface SeasonProgress {
  discipline: string;
  races_done: number;
  races_total: number;
}

export const standings = {
  get: (gender: "Men" | "Women", season?: string) =>
    request<StandingsResponse>(`/standings/${gender}${season ? `?season=${season}` : ""}`),

  progress: (gender: "Men" | "Women", season?: string) =>
    request<SeasonProgress[]>(`/standings/${gender}/progress${season ? `?season=${season}` : ""}`),
};
