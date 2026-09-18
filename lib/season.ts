// ─── Types ───────────────────────────────────────────────────────────────────

export interface SeasonInfo {
  code: string;   // ex. "2526"
  label: string;  // ex. "2025/26"
}

// ─── Saisons passées connues (à compléter chaque année) ──────────────────────

export const KNOWN_PAST_SEASONS: SeasonInfo[] = [
  { code: "2526", label: "2025/26" },
];

// ─── Deadlines pronostics saison, par code de saison ──────────────────────────
// Miroir de PRONOS_DEADLINE_BY_SEASON (utils/biathlon_data.py) — à compléter à
// chaque nouvelle saison, en même temps que côté backend. Veille de la 1ère
// course, 23:59.

const PRONOS_DEADLINE_BY_SEASON: Record<string, string> = {
  "2526": "2025-11-27T23:59:00", // Veille de la 1ère course (Östersund, 28 nov 2025)
  "2627": "2026-11-25T23:59:00", // Veille de la 1ère course (Kontiolahti, 26 nov 2026)
};

/** Deadline des pronos pour une saison, ou null si pas encore connue (saison à compléter ci-dessus). */
export function getPronosDeadline(seasonCode: string): Date | null {
  const iso = PRONOS_DEADLINE_BY_SEASON[seasonCode];
  return iso ? new Date(iso) : null;
}

// ─── Calcul de la saison courante depuis la date ──────────────────────────────
//
//  Nov X → Avr X+1  : saison X/X+1 active (pronos modifiables)
//  Mai X+1 → Oct X+1 : hors-saison (sablier, saison X+1/X+2 "future")

export function computeCurrentSeason(date = new Date()): {
  season: SeasonInfo;
  isOffSeason: boolean;
} {
  const year = date.getFullYear();
  const month = date.getMonth() + 1; // 1-12

  // Mai (5) inclus → Oct (10) inclus = hors-saison
  const isOffSeason = month >= 5 && month < 11;

  let startYear: number;
  if (month >= 11) {
    startYear = year;          // Nov-Déc : saison démarre cette année
  } else if (month < 5) {
    startYear = year - 1;      // Jan-Avr : saison a démarré l'année dernière
  } else {
    startYear = year;          // Hors-saison : on pointe sur la prochaine saison
  }

  const y1 = String(startYear).slice(2);
  const y2 = String(startYear + 1).slice(2);

  return {
    season: { code: `${y1}${y2}`, label: `${startYear}/${y2}` },
    isOffSeason,
  };
}

// ─── Liste des saisons disponibles dans le sélecteur ─────────────────────────

export function getAvailableSeasons(currentSeason: SeasonInfo): SeasonInfo[] {
  // Saison courante/future en tête, puis les archives dans l'ordre antechronologique
  const all: SeasonInfo[] = [currentSeason];
  for (const s of KNOWN_PAST_SEASONS) {
    if (!all.find((x) => x.code === s.code)) all.push(s);
  }
  return all;
}
