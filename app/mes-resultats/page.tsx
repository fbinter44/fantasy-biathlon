"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useSeason } from "@/context/SeasonContext";
import { classement, leagues, PlayerPoints } from "@/lib/api";
import SeasonGuard from "@/components/SeasonGuard";

interface LeagueRank {
  league_id: string;
  name: string;
  rank: number;
  total: number;
}

const EDGE_SIZE = 3;      // nb de joueurs affichés en haut / en bas
const NEIGHBOR_SIZE = 1;  // nb de voisins affichés autour de mon rang

function ScoreCard({
  icon, label, value, highlight = false,
}: { icon: string; label: string; value: number; highlight?: boolean }) {
  return (
    <div className={`rounded-2xl border shadow-sm p-4 text-center ${
      highlight ? "bg-blue-50 border-blue-200" : "bg-white border-gray-200"
    }`}>
      <div className="text-2xl mb-1">{icon}</div>
      <div className={`text-lg font-bold ${highlight ? "text-blue-700" : "text-gray-900"}`}>{value}</div>
      <div className="text-xs text-gray-400">{label}</div>
    </div>
  );
}

type SortKey = "total_points" | "men_points" | "women_points" | "globe_points" | "race_points";

const COLUMNS: { key: SortKey; label: string }[] = [
  { key: "total_points", label: "Total" },
  { key: "men_points",   label: "Hommes" },
  { key: "women_points", label: "Femmes" },
  { key: "globe_points", label: "Globes" },
  { key: "race_points",  label: "Courses" },
];

export default function MesResultatsPage() {
  const { user, loading: authLoading } = useAuth();
  const { selected } = useSeason();
  const router = useRouter();

  const [myLeagueRanks, setMyLeagueRanks] = useState<LeagueRank[]>([]);
  const [globalRanking, setGlobalRanking] = useState<PlayerPoints[]>([]);
  const [loading, setLoading] = useState(true);
  const [showFullRanking, setShowFullRanking] = useState(false);
  const [sortKey, setSortKey] = useState<SortKey>("total_points");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  function toggleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir((d) => (d === "desc" ? "asc" : "desc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  useEffect(() => {
    if (authLoading) return;
    if (!user) { router.push("/login"); return; }

    async function load() {
      try {
        const [myLeagues, global] = await Promise.all([
          leagues.mine(user!.token),
          classement.global(selected.code),
        ]);
        setGlobalRanking(global);

        const perLeague = await Promise.all(
          myLeagues.map(async (lg): Promise<LeagueRank | null> => {
            const ranked = await classement.league(lg.league_id, user!.token, selected.code);
            const mine = ranked.find((p) => p.user_id === user!.user_id);
            return mine ? { league_id: lg.league_id, name: lg.name, rank: mine.rank, total: ranked.length } : null;
          })
        );
        setMyLeagueRanks(perLeague.filter((r): r is LeagueRank => r !== null));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [user, authLoading, router, selected.code]);

  const myGlobal = globalRanking.find((p) => p.user_id === user?.user_id);

  if (loading) return (
    <div className="flex justify-center items-center min-h-[60vh] text-gray-400">Chargement...</div>
  );

  // Fenêtre autour de mon rang : premiers · … · voisins · … · derniers.
  // On construit l'ensemble des indices à afficher (bords + voisinage), puis on
  // insère un "gap" à chaque rupture de continuité — gère nativement les listes
  // courtes et les chevauchements (ligue de 5 joueurs, moi dans le top 3, etc.).
  let windowRows: (PlayerPoints | "gap")[] = globalRanking;
  if (myGlobal) {
    const myIdx = myGlobal.rank - 1;
    const included = new Set<number>();
    for (let i = 0; i < EDGE_SIZE; i++) included.add(i);
    for (let i = globalRanking.length - EDGE_SIZE; i < globalRanking.length; i++) included.add(i);
    for (let i = myIdx - NEIGHBOR_SIZE; i <= myIdx + NEIGHBOR_SIZE; i++) included.add(i);

    const indices = [...included]
      .filter((i) => i >= 0 && i < globalRanking.length)
      .sort((a, b) => a - b);

    windowRows = [];
    let prev = -1;
    for (const i of indices) {
      if (prev !== -1 && i > prev + 1) windowRows.push("gap");
      windowRows.push(globalRanking[i]);
      prev = i;
    }
  }

  const isTruncated = globalRanking.length > windowRows.filter((r) => r !== "gap").length;

  const sortedFullRanking = [...globalRanking].sort(
    (a, b) => (a[sortKey] - b[sortKey]) * (sortDir === "asc" ? 1 : -1)
  );

  // Le mode compact (premiers · … · voisins · … · derniers) n'a de sens que
  // trié par total décroissant (l'ordre dans lequel `rank` a été calculé) —
  // dès qu'on change de tri, on bascule sur le tableau complet.
  const isDefaultSort = sortKey === "total_points" && sortDir === "desc";
  const showFullTable = showFullRanking || !isDefaultSort;
  const rows: (PlayerPoints | "gap")[] = showFullTable ? sortedFullRanking : windowRows;

  function resetToCompact() {
    setShowFullRanking(false);
    setSortKey("total_points");
    setSortDir("desc");
  }

  return (
    <SeasonGuard>
      <main className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">📊 Mes Résultats</h1>

        {/* Mon classement par ski club */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5 mb-6">
          <h2 className="font-semibold text-gray-800 mb-4">🏔️ Mon classement par ski club</h2>
          {myLeagueRanks.length === 0 ? (
            <p className="text-sm text-gray-400">Tu n&apos;es dans aucun ski club pour l&apos;instant.</p>
          ) : (
            <div className="space-y-2">
              {myLeagueRanks.map((lg) => (
                <div key={lg.league_id} className="flex items-center justify-between px-3 py-2 rounded-lg bg-gray-50">
                  <span className="text-sm text-gray-700">{lg.name}</span>
                  <span className="text-sm font-semibold text-blue-600">{lg.rank}e sur {lg.total}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Détail du score */}
        {myGlobal && (
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-6">
            <ScoreCard icon="🏆" label="Total" value={myGlobal.total_points} highlight />
            <ScoreCard icon="🧔" label="Points Hommes" value={myGlobal.men_points} />
            <ScoreCard icon="👩" label="Points Femmes" value={myGlobal.women_points} />
            <ScoreCard icon="🌍" label="Points Globes" value={myGlobal.globe_points} />
            <ScoreCard icon="🎯" label="Points Courses" value={myGlobal.race_points} />
          </div>
        )}

        {/* Classement général, indépendant des ski clubs */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-800">🌍 Classement général</h2>
            {myGlobal && (
              <span className="text-sm font-semibold text-blue-600">
                {myGlobal.rank}e sur {globalRanking.length}
              </span>
            )}
          </div>

          <div className="overflow-x-auto -mx-2">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-400 border-b border-gray-100">
                  <th className="py-2 px-2 font-medium">#</th>
                  <th className="py-2 px-2 font-medium">Joueur</th>
                  {COLUMNS.map((col) => (
                    <th key={col.key} className="py-2 px-2 font-medium">
                      <button
                        onClick={() => toggleSort(col.key)}
                        className={`flex items-center gap-1 hover:text-gray-700 transition-colors ${
                          sortKey === col.key ? "text-blue-600 font-semibold" : ""
                        }`}
                      >
                        {col.label}
                        {sortKey === col.key && <span>{sortDir === "desc" ? "▼" : "▲"}</span>}
                      </button>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {rows.map((row, i) =>
                  row === "gap" ? (
                    <tr key={`gap-${i}`}>
                      <td colSpan={2 + COLUMNS.length} className="py-2 text-center text-gray-300">···</td>
                    </tr>
                  ) : (
                    <tr key={row.user_id} className={row.user_id === user?.user_id ? "bg-blue-50" : ""}>
                      <td className="py-2 px-2 text-gray-400">{showFullTable ? i + 1 : row.rank}</td>
                      <td className="py-2 px-2 text-gray-700">{row.username}</td>
                      <td className="py-2 px-2 font-medium text-gray-900">{row.total_points}</td>
                      <td className="py-2 px-2 text-gray-600">{row.men_points}</td>
                      <td className="py-2 px-2 text-gray-600">{row.women_points}</td>
                      <td className="py-2 px-2 text-gray-600">{row.globe_points}</td>
                      <td className="py-2 px-2 text-gray-600">{row.race_points}</td>
                    </tr>
                  )
                )}
              </tbody>
            </table>
          </div>

          {isTruncated && !showFullTable && (
            <button
              onClick={() => setShowFullRanking(true)}
              className="mt-4 text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              Voir le classement complet →
            </button>
          )}
          {showFullTable && (
            <button
              onClick={resetToCompact}
              className="mt-4 text-sm text-gray-400 hover:text-gray-600"
            >
              Réduire
            </button>
          )}
        </div>
      </main>
    </SeasonGuard>
  );
}
