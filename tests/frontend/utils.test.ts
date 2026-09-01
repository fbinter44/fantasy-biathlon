import { describe, it, expect } from "vitest";
import {
  parseApiError,
  buildChartData,
  computeBiathletStats,
  countFilledPronos,
  hasDuplicates,
} from "@/lib/utils";
import type { VenueEvolution, PronosticsResponse } from "@/lib/api";

// ─── parseApiError ────────────────────────────────────────────────────────────

describe("parseApiError", () => {
  it("retourne le message string depuis detail", () => {
    expect(parseApiError({ detail: "Utilisateur introuvable." }, 404))
      .toBe("Utilisateur introuvable.");
  });

  it("joint les messages d'un tableau de validation 422", () => {
    const body = { detail: [{ msg: "champ requis" }, { msg: "email invalide" }] };
    expect(parseApiError(body, 422)).toBe("champ requis, email invalide");
  });

  it("retourne 'Erreur N' si pas de detail", () => {
    expect(parseApiError({}, 500)).toBe("Erreur 500");
  });

  it("retourne 'Erreur N' si body est null", () => {
    expect(parseApiError(null, 503)).toBe("Erreur 503");
  });

  it("gère un tableau vide de validations", () => {
    expect(parseApiError({ detail: [] }, 422)).toBe("");
  });
});

// ─── buildChartData ───────────────────────────────────────────────────────────

const makePlayer = (user_id: string, username: string, pts: number) => ({
  user_id, username,
  total_points: pts, men_points: 0, women_points: 0, globe_points: 0, race_points: 0, rank: 1,
});

const makeVenue = (index: number, name: string, players: ReturnType<typeof makePlayer>[]): VenueEvolution => ({
  index, name, start_date: "2025-11-01", end_date: "2025-11-03", players,
});

describe("buildChartData", () => {
  it("utilise le nom de venue comme clé", () => {
    const evo = [makeVenue(1, "Östersund", [makePlayer("u1", "Alice", 100)])];
    const { chartData } = buildChartData(evo, null);
    expect(chartData[0].venue).toBe("Östersund");
  });

  it("liste tous les joueurs", () => {
    const evo = [makeVenue(1, "Oslo", [
      makePlayer("u1", "Alice", 100),
      makePlayer("u2", "Bob", 80),
    ])];
    const { players } = buildChartData(evo, null);
    expect(players).toContain("Alice");
    expect(players).toContain("Bob");
  });

  it("filtre par memberIds", () => {
    const evo = [makeVenue(1, "Oslo", [
      makePlayer("u1", "Alice", 100),
      makePlayer("u2", "Bob", 80),
    ])];
    const { players } = buildChartData(evo, new Set(["u1"]));
    expect(players).toContain("Alice");
    expect(players).not.toContain("Bob");
  });

  it("les points sont dans les lignes du chart", () => {
    const evo = [makeVenue(1, "Oslo", [makePlayer("u1", "Alice", 150)])];
    const { chartData } = buildChartData(evo, null);
    expect(chartData[0]["Alice"]).toBe(150);
  });

  it("retourne une ligne par venue", () => {
    const evo = [
      makeVenue(1, "Östersund", [makePlayer("u1", "Alice", 100)]),
      makeVenue(2, "Hochfilzen", [makePlayer("u1", "Alice", 200)]),
    ];
    const { chartData } = buildChartData(evo, null);
    expect(chartData).toHaveLength(2);
  });

  it("evolution vide → chartData vide et players vide", () => {
    const { chartData, players } = buildChartData([], null);
    expect(chartData).toHaveLength(0);
    expect(players).toHaveLength(0);
  });
});

// ─── computeBiathletStats ────────────────────────────────────────────────────

const makeProno = (userId: string, top5h: string[], top5f: string[], globes: Partial<PronosticsResponse["globes"]> = {}): PronosticsResponse => ({
  user_id: userId,
  username: `user_${userId}`,
  top5_h: { p1: top5h[0] ?? "", p2: top5h[1] ?? "", p3: top5h[2] ?? "", p4: top5h[3] ?? "", p5: top5h[4] ?? "" },
  top5_f: { p1: top5f[0] ?? "", p2: top5f[1] ?? "", p3: top5f[2] ?? "", p4: top5f[3] ?? "", p5: top5f[4] ?? "" },
  globes: {
    sprint_h: "", sprint_f: "", pursuit_h: "", pursuit_f: "",
    individual_h: "", individual_f: "", mass_start_h: "", mass_start_f: "",
    ...globes,
  },
});

describe("computeBiathletStats", () => {
  it("athlète absent → tout à zéro", () => {
    const data = [makeProno("u1", ["A", "B", "C", "D", "E"], [])];
    const stats = computeBiathletStats(data, "Z", "u1");
    expect(stats.top5.total).toBe(0);
    expect(stats.top5.p1).toBe(0);
  });

  it("compte les sélections top 5 correctement", () => {
    const data = [
      makeProno("u1", ["A", "B", "C", "D", "E"], []),
      makeProno("u2", ["B", "A", "C", "D", "E"], []),
    ];
    const stats = computeBiathletStats(data, "A", "u1");
    expect(stats.top5.total).toBe(2);  // u1 et u2 ont tous les deux A
    expect(stats.top5.p1).toBe(1);     // u1 a mis A en 1er
  });

  it("détecte ma position dans le top 5", () => {
    const data = [makeProno("me", ["X", "TARGET", "Y", "Z", "W"], [])];
    const stats = computeBiathletStats(data, "TARGET", "me");
    expect(stats.myTop5Place).toBe(2);
  });

  it("myTop5Place est null si je n'ai pas mis l'athlète", () => {
    const data = [makeProno("me", ["A", "B", "C", "D", "E"], [])];
    const stats = computeBiathletStats(data, "Z", "me");
    expect(stats.myTop5Place).toBeNull();
  });

  it("compte les votes globe sprint", () => {
    const data = [
      makeProno("u1", [], [], { sprint_h: "STAR" }),
      makeProno("u2", [], [], { sprint_h: "OTHER" }),
      makeProno("u3", [], [], { sprint_f: "STAR" }),
    ];
    const stats = computeBiathletStats(data, "STAR", "u1");
    expect(stats.globes.sprint).toBe(2);  // u1 (sprint_h) + u3 (sprint_f)
  });

  it("détecte mon vote globe", () => {
    const data = [makeProno("me", [], [], { pursuit_h: "STAR" })];
    const stats = computeBiathletStats(data, "STAR", "me");
    expect(stats.myGlobes.pursuit).toBe(true);
    expect(stats.myGlobes.sprint).toBe(false);
  });

  it("total = nombre de joueurs dans la liste", () => {
    const data = [makeProno("u1", [], []), makeProno("u2", [], [])];
    const stats = computeBiathletStats(data, "X", "u1");
    expect(stats.total).toBe(2);
  });
});

// ─── countFilledPronos ────────────────────────────────────────────────────────

describe("countFilledPronos", () => {
  it("0 quand tout est vide", () => {
    const empty = { p1: "", p2: "", p3: "", p4: "", p5: "" };
    const emptyGlobes = { sprint_h: "", sprint_f: "", pursuit_h: "", pursuit_f: "",
                          individual_h: "", individual_f: "", mass_start_h: "", mass_start_f: "" };
    expect(countFilledPronos(empty, empty, emptyGlobes)).toBe(0);
  });

  it("18 quand tout est rempli", () => {
    const full5 = { p1: "A", p2: "B", p3: "C", p4: "D", p5: "E" };
    const fullGlobes = { sprint_h: "A", sprint_f: "B", pursuit_h: "C", pursuit_f: "D",
                         individual_h: "E", individual_f: "F", mass_start_h: "G", mass_start_f: "H" };
    expect(countFilledPronos(full5, full5, fullGlobes)).toBe(18);
  });

  it("compte correctement un remplissage partiel", () => {
    const partial = { p1: "A", p2: "B", p3: "", p4: "", p5: "" };
    const emptyGlobes = { sprint_h: "", sprint_f: "", pursuit_h: "", pursuit_f: "",
                          individual_h: "", individual_f: "", mass_start_h: "", mass_start_f: "" };
    expect(countFilledPronos(partial, partial, emptyGlobes)).toBe(4);
  });
});

// ─── hasDuplicates ────────────────────────────────────────────────────────────

describe("hasDuplicates", () => {
  it("false quand pas de doublons", () => {
    expect(hasDuplicates({ p1: "A", p2: "B", p3: "C", p4: "D", p5: "E" })).toBe(false);
  });

  it("true quand doublon", () => {
    expect(hasDuplicates({ p1: "A", p2: "A", p3: "C", p4: "D", p5: "E" })).toBe(true);
  });

  it("false quand champs vides (pas comptés)", () => {
    expect(hasDuplicates({ p1: "A", p2: "", p3: "", p4: "", p5: "" })).toBe(false);
  });

  it("false quand tout est vide", () => {
    expect(hasDuplicates({ p1: "", p2: "", p3: "", p4: "", p5: "" })).toBe(false);
  });
});
