"use client";

import { type ReactNode } from "react";
import { useSeason } from "@/context/SeasonContext";

/**
 * À wrapper autour du contenu des pages "saisonnières".
 * Affiche un sablier si la saison sélectionnée est la prochaine (pas encore commencée).
 */
export default function SeasonGuard({ children }: { children: ReactNode }) {
  const { isFutureSeason, selected } = useSeason();

  if (!isFutureSeason) return <>{children}</>;

  return (
    <main className="max-w-2xl mx-auto px-4 py-20 flex flex-col items-center text-center">
      <div className="text-7xl mb-6 animate-spin" style={{ animationDuration: "4s" }}>⏳</div>
      <h1 className="text-2xl font-bold text-gray-800 mb-3">
        La saison {selected.label} n&apos;a pas encore débuté
      </h1>
      <p className="text-gray-500 text-sm leading-relaxed max-w-sm">
        Reviens à partir du <strong>1er novembre</strong> pour soumettre tes pronostics
        et suivre la saison en direct.
      </p>
      <p className="mt-6 text-xs text-gray-400">
        En attendant, tu peux consulter les saisons précédentes depuis le sélecteur de saison.
      </p>
    </main>
  );
}
