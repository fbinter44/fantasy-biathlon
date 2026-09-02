"use client";

import { type ReactNode } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { useSeason } from "@/context/SeasonContext";
import { useAuth } from "@/context/AuthContext";

// Pages toujours accessibles même pendant le hors-saison
const BYPASS_PATHS = ["/login", "/reset-password", "/reglement", "/compte", "/ligues", "/calendrier"];

/**
 * Guard global positionné dans le layout.
 * Si la saison sélectionnée est la prochaine (pas encore démarrée),
 * bloque toutes les pages de l'app (sauf auth + statiques) et affiche le sablier.
 * Avantage : aucun appel API ne part depuis les pages enfants.
 */
export default function AppGuard({ children }: { children: ReactNode }) {
  const { isFutureSeason, selected } = useSeason();
  const { user } = useAuth();
  const pathname = usePathname();

  const isBypassed = BYPASS_PATHS.some((p) => pathname?.startsWith(p));

  if (isFutureSeason && !isBypassed) {
    return (
      <main className="max-w-2xl mx-auto px-4 py-20 flex flex-col items-center text-center">
        <div className="text-7xl mb-6 animate-spin" style={{ animationDuration: "4s" }}>
          ⏳
        </div>
        <h1 className="text-2xl font-bold text-gray-800 mb-3">
          La saison {selected.label} n&apos;a pas encore débuté
        </h1>
        <p className="text-gray-500 text-sm leading-relaxed max-w-sm">
          Reviens à partir du <strong>1er novembre</strong> pour soumettre tes pronostics
          et suivre la saison en direct.
        </p>
        <p className="mt-4 text-xs text-gray-400">
          En attendant, tu peux consulter les saisons précédentes depuis le sélecteur de saison.
        </p>

        {/* Liens utiles */}
        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          {!user && (
            <Link
              href="/login"
              className="px-5 py-2 rounded-xl bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors"
            >
              Se connecter
            </Link>
          )}
          <Link
            href="/ligues"
            className="px-5 py-2 rounded-xl border border-gray-300 text-gray-600 text-sm font-medium hover:bg-gray-100 transition-colors"
          >
            🏔️ Mes Ski Clubs
          </Link>
          <Link
            href="/calendrier"
            className="px-5 py-2 rounded-xl border border-gray-300 text-gray-600 text-sm font-medium hover:bg-gray-100 transition-colors"
          >
            📅 Calendrier
          </Link>
        </div>
        <p className="mt-3 text-xs text-gray-400">
          Ces deux pages restent accessibles pendant la trêve.
        </p>
      </main>
    );
  }

  return <>{children}</>;
}
