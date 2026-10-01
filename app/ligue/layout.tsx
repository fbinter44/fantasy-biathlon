"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useSeason } from "@/context/SeasonContext";

/**
 * Garde partagée par toutes les pages /ligue/* (Pronos du Ski Club, Focus
 * Biathlète, Classement du Ski Club, Détail des scores...).
 *
 * Le menu du Header masque déjà ces liens tant que les pronos saison ne sont
 * pas remplis (voir `leagueAccessible` dans components/Header.tsx, même
 * formule reprise ici) — mais ça ne protège que la NAVIGATION vers ces pages,
 * pas leur affichage une fois dessus : un joueur resté sur une page /ligue/*
 * après avoir consulté une saison archivée (toujours accessible) pouvait
 * rebasculer sur la saison en cours (pronos pas encore remplis) via le
 * sélecteur sans être éjecté. Cette garde réagit au changement de saison et
 * redirige vers Mes Pronos à chaque fois que la condition n'est plus remplie.
 */
export default function LigueLayout({ children }: { children: ReactNode }) {
  const { user, loading: authLoading, hasPronos, currentLeague } = useAuth();
  const { selected, defaultSeason } = useSeason();
  const router = useRouter();

  const leagueAccessible = hasPronos || selected.code !== defaultSeason.code;
  const blocked = !!currentLeague && !leagueAccessible;

  useEffect(() => {
    if (authLoading || !user) return;
    if (blocked) router.replace("/pronostics?pronos_requis=1");
  }, [authLoading, user, blocked, router]);

  if (!authLoading && user && blocked) {
    return (
      <main className="max-w-md mx-auto px-4 py-20 text-center">
        <div className="text-5xl mb-4">📝</div>
        <h1 className="text-xl font-bold text-gray-800 mb-2">Remplis d&apos;abord tes pronos</h1>
        <p className="text-gray-500 text-sm">Redirection vers Mes Pronos…</p>
      </main>
    );
  }

  return <>{children}</>;
}
