/**
 * Fonctions utilitaires pures — testables sans DOM ni React.
 */

import type { PlayerPoints, VenueEvolution, PronosticsResponse } from "@/lib/api";

// ─── Erreurs API ──────────────────────────────────────────────────────────────

/**
 * Extrait un message lisible depuis une réponse d'erreur FastAPI.
 * FastAPI retourne soit { detail: "string" } soit { detail: [...] } (validation 422).
 */
export function parseApiError(body: unknown, status: number): string {
  if (typeof body === "object" && body !== null && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (Array.isArray(detail)) {
      return detail.map((e: { msg?: string }) => e.msg ?? "Erreur").join(", ");
    }
    if (typeof detail === "string") return detail;
  }
  return `Erreur ${status}`;
}

// ─── Évolution classement ────────────────────────────────────────────────────

export type ChartRow = Record<string, string | number>;

export function buildChartData(
  evolution: VenueEvolution[],
  memberIds: Set<string> | null
): { chartData: ChartRow[]; players: string[] } {
  const playerMap = new Map<string, string>();
  evolution.forEach((v) => {
    v.players.forEach((p) => {
      if (!memberIds || memberIds.has(p.user_id)) playerMap.set(p.user_id, p.username);
    });
  });
  const chartData = evolution.map((v) => {
    const row: ChartRow = { venue: v.name };
    v.players.forEach((p) => {
      if (!memberIds || memberIds.has(p.user_id)) row[p.username] = p.total_points;
    });
    return row;
  });
  return { chartData, players: Array.from(playerMap.values()) };
}

// ─── Focus biathlète ─────────────────────────────────────────────────────────

export interface BiathletStats {
  top5: { p1: number; p2: number; p3: number; p4: number; p5: number; total: number };
  globes: { sprint: number; pursuit: number; individual: number; mass_start: number };
  myTop5Place: number | null;
  myGlobes: { sprint: boolean; pursuit: boolean; individual: boolean; mass_start: boolean };
  total: number;
}

export function computeBiathletStats(
  data: PronosticsResponse[],
  ibuId: string,
  myUserId: string
): BiathletStats {
  const stats: BiathletStats = {
    top5: { p1: 0, p2: 0, p3: 0, p4: 0, p5: 0, total: 0 },
    globes: { sprint: 0, pursuit: 0, individual: 0, mass_start: 0 },
    myTop5Place: null,
    myGlobes: { sprint: false, pursuit: false, individual: false, mass_start: false },
    total: data.length,
  };

  data.forEach((p) => {
    const isMe = p.user_id === myUserId;
    const all = [
      p.top5_h.p1, p.top5_h.p2, p.top5_h.p3, p.top5_h.p4, p.top5_h.p5,
      p.top5_f.p1, p.top5_f.p2, p.top5_f.p3, p.top5_f.p4, p.top5_f.p5,
    ];
    all.forEach((id, i) => {
      if (id !== ibuId) return;
      const pos = (i % 5) + 1;
      (stats.top5 as Record<string, number>)[`p${pos}`]++;
      stats.top5.total++;
      if (isMe) stats.myTop5Place = pos;
    });

    const globeFields: [keyof typeof stats.globes, string][] = [
      ["sprint", p.globes.sprint_h], ["sprint", p.globes.sprint_f],
      ["pursuit", p.globes.pursuit_h], ["pursuit", p.globes.pursuit_f],
      ["individual", p.globes.individual_h], ["individual", p.globes.individual_f],
      ["mass_start", p.globes.mass_start_h], ["mass_start", p.globes.mass_start_f],
    ];
    globeFields.forEach(([disc, id]) => {
      if (id === ibuId) {
        stats.globes[disc]++;
        if (isMe) stats.myGlobes[disc] = true;
      }
    });
  });

  return stats;
}

// ─── Progression pronostics ───────────────────────────────────────────────────

/** Calcule le nombre de champs remplis parmi les 18 attendus. */
export function countFilledPronos(
  top5h: Record<string, string>,
  top5f: Record<string, string>,
  globes: Record<string, string>
): number {
  return (
    Object.values(top5h).filter(Boolean).length +
    Object.values(top5f).filter(Boolean).length +
    Object.values(globes).filter(Boolean).length
  );
}

/** Vérifie si un top 5 contient des doublons (hors chaînes vides). */
export function hasDuplicates(top5: Record<string, string>): boolean {
  const values = Object.values(top5).filter(Boolean);
  return new Set(values).size !== values.length;
}
