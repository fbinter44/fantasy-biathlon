"use client";

import { createContext, useContext, useState, type ReactNode } from "react";
import {
  type SeasonInfo,
  computeCurrentSeason,
  getAvailableSeasons,
  KNOWN_PAST_SEASONS,
} from "@/lib/season";

// ─── Types ────────────────────────────────────────────────────────────────────

interface SeasonContextValue {
  /** Saison actuellement affichée (peut être passée ou future) */
  selected: SeasonInfo;
  setSelected: (s: SeasonInfo) => void;
  /** Saison calculée depuis la date du jour (active ou future selon la période) */
  defaultSeason: SeasonInfo;
  /** On est entre Mai et Nov : aucune saison active, la prochaine n'a pas démarré */
  isOffSeason: boolean;
  /** La saison sélectionnée est la future (sablier à afficher) */
  isFutureSeason: boolean;
  /** Consultation seulement : saison passée OU hors-saison */
  isReadOnly: boolean;
  /** Liste pour le sélecteur (courante/future en tête, archives ensuite) */
  availableSeasons: SeasonInfo[];
}

// ─── Contexte ─────────────────────────────────────────────────────────────────

const SeasonContext = createContext<SeasonContextValue | null>(null);

export function SeasonProvider({ children }: { children: ReactNode }) {
  const { season: defaultSeason, isOffSeason } = computeCurrentSeason();
  const availableSeasons = getAvailableSeasons(defaultSeason);

  const [selected, setSelected] = useState<SeasonInfo>(defaultSeason);

  // Saison future = on est hors-saison ET la saison sélectionnée n'est pas une saison passée connue
  const isFutureSeason =
    isOffSeason &&
    !KNOWN_PAST_SEASONS.find((s) => s.code === selected.code);

  // Lecture seule si : hors-saison active OU on consulte une saison différente de la saison courante
  const isReadOnly = isOffSeason || selected.code !== defaultSeason.code;

  return (
    <SeasonContext.Provider
      value={{
        selected,
        setSelected,
        defaultSeason,
        isOffSeason,
        isFutureSeason,
        isReadOnly,
        availableSeasons,
      }}
    >
      {children}
    </SeasonContext.Provider>
  );
}

export function useSeason() {
  const ctx = useContext(SeasonContext);
  if (!ctx) throw new Error("useSeason doit être utilisé dans SeasonProvider");
  return ctx;
}
