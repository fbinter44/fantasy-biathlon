import { describe, it, expect } from "vitest";
import { computeCurrentSeason, getPronosDeadline, getAvailableSeasons } from "@/lib/season";

// computeCurrentSeason() est le miroir TS de current_ibu_season_code()
// (utils/biathlon_data.py) — les deux DOIVENT retomber sur le même code pour
// la même date. Aucun test ne couvrait cette logique avant, alors qu'elle a
// été modifiée en cours de projet (bascule hors-saison déplacée du 1er nov
// au 1er oct) — ces cas verrouillent le comportement actuel des deux côtés.

describe("computeCurrentSeason", () => {
  it("janvier → saison démarrée l'année précédente, pas hors-saison", () => {
    const { season, isOffSeason } = computeCurrentSeason(new Date(2026, 0, 15));
    expect(season.code).toBe("2526");
    expect(isOffSeason).toBe(false);
  });

  it("30 avril → encore l'ancienne saison, pas hors-saison", () => {
    const { season, isOffSeason } = computeCurrentSeason(new Date(2026, 3, 30));
    expect(season.code).toBe("2526");
    expect(isOffSeason).toBe(false);
  });

  it("1er mai → bascule hors-saison, saison suivante déjà affichée", () => {
    const { season, isOffSeason } = computeCurrentSeason(new Date(2026, 4, 1));
    expect(season.code).toBe("2627");
    expect(isOffSeason).toBe(true);
  });

  it("30 septembre → toujours hors-saison", () => {
    const { season, isOffSeason } = computeCurrentSeason(new Date(2026, 8, 30));
    expect(season.code).toBe("2627");
    expect(isOffSeason).toBe(true);
  });

  it("1er octobre → fin du hors-saison, saison suivante démarre", () => {
    const { season, isOffSeason } = computeCurrentSeason(new Date(2026, 9, 1));
    expect(season.code).toBe("2627");
    expect(isOffSeason).toBe(false);
  });

  it("31 décembre → saison en cours, pas hors-saison", () => {
    const { season, isOffSeason } = computeCurrentSeason(new Date(2026, 11, 31));
    expect(season.code).toBe("2627");
    expect(isOffSeason).toBe(false);
  });

  it("label correspond au code", () => {
    const { season } = computeCurrentSeason(new Date(2026, 0, 15));
    expect(season.label).toBe("2025/26");
  });
});

describe("getPronosDeadline", () => {
  it("retourne la date pour une saison connue", () => {
    const d = getPronosDeadline("2526");
    expect(d).not.toBeNull();
    expect(d?.getFullYear()).toBe(2025);
  });

  it("retourne null pour une saison inconnue (fail-closed)", () => {
    expect(getPronosDeadline("9999")).toBeNull();
  });
});

describe("getAvailableSeasons", () => {
  it("place la saison courante en tête", () => {
    const current = { code: "2627", label: "2026/27" };
    const seasons = getAvailableSeasons(current);
    expect(seasons[0]).toEqual(current);
  });

  it("n'ajoute pas de doublon si la saison courante est déjà une saison archivée connue", () => {
    const current = { code: "2526", label: "2025/26" };
    const seasons = getAvailableSeasons(current);
    const count = seasons.filter((s) => s.code === "2526").length;
    expect(count).toBe(1);
  });
});
