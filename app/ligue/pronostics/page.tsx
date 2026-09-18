"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { pronostics, leagues, athletes, PronosticsResponse, AthleteResponse } from "@/lib/api";
import { useSeason } from "@/context/SeasonContext";
import SeasonGuard from "@/components/SeasonGuard";
import Flag from "@/components/Flag";

type Mode = "top5h" | "top5f" | "globesh" | "globesf";

const MODES: { key: Mode; label: string; icon: string }[] = [
  { key: "top5h",   label: "Top 5 Hommes", icon: "🧔" },
  { key: "top5f",   label: "Top 5 Femmes", icon: "👩" },
  { key: "globesh", label: "Globes Hommes", icon: "🌍" },
  { key: "globesf", label: "Globes Femmes", icon: "🌍" },
];

const RANK_STYLES = [
  { bg: "bg-yellow-400", text: "text-yellow-900", label: "1er" },
  { bg: "bg-gray-300",   text: "text-gray-700",   label: "2e"  },
  { bg: "bg-amber-600",  text: "text-amber-50",   label: "3e"  },
  { bg: "bg-gray-100",   text: "text-gray-500",   label: "4e"  },
  { bg: "bg-gray-100",   text: "text-gray-500",   label: "5e"  },
];

const GLOBE_COLS = [
  { icon: "⚡", label: "Sprint"     },
  { icon: "🎿", label: "Poursuite"  },
  { icon: "🎯", label: "Individuel" },
  { icon: "🏁", label: "Mass Start" },
];

function AthleteCell({ ibuId, map }: { ibuId: string; map: Record<string, AthleteResponse> }) {
  const a = map[ibuId];
  if (!a) return <span className="text-gray-300">—</span>;
  return (
    <span className="inline-flex items-center gap-1.5">
      <Flag nation={a.nation} />
      {a.family_name} {a.given_name}
    </span>
  );
}

export default function PronosSkiClubPage() {
  const { user, currentLeague } = useAuth();
  const { selected } = useSeason();
  const router = useRouter();

  const [data, setData] = useState<PronosticsResponse[]>([]);
  const [athMap, setAthMap] = useState<Record<string, AthleteResponse>>({});
  const [mode, setMode] = useState<Mode>("top5h");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) { router.push("/login"); return; }

    async function load() {
      try {
        const [all, ath] = await Promise.all([pronostics.all(selected.code), athletes.list()]);
        const map: Record<string, AthleteResponse> = {};
        (ath as AthleteResponse[]).forEach((a) => { map[a.ibu_id] = a; });
        setAthMap(map);

        if (currentLeague) {
          const league = await leagues.get(currentLeague.league_id, user!.token);
          const memberIds = new Set(league.members.map((m) => m.user_id));
          setData(all.filter((p) => memberIds.has(p.user_id)));
        } else {
          setData(all);
        }
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [user, currentLeague, router]);

  // Trier : moi en premier
  const sorted = [...data].sort((a, b) =>
    a.user_id === user?.user_id ? -1 : b.user_id === user?.user_id ? 1 : 0
  );

  if (loading) return (
    <div className="flex justify-center items-center min-h-[60vh] text-gray-400">Chargement...</div>
  );

  return (
    <SeasonGuard>
    <main className="max-w-7xl mx-auto px-4 py-8">
      {/* Titre */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">🏔️ Les Pronos du Ski Club</h1>
        {currentLeague && (
          <p className="text-sm text-gray-500 mt-1">
            {currentLeague.name} · {data.length} joueur{data.length > 1 ? "s" : ""}
          </p>
        )}
      </div>

      {!currentLeague && (
        <div className="mb-6 p-4 bg-blue-50 border-l-4 border-blue-400 rounded-xl text-blue-800 text-sm">
          <b>ℹ️</b> Sélectionne un ski club pour voir les pronos de ta ligue.
        </div>
      )}

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 mb-6">
        {MODES.map(({ key, label: mLabel, icon }) => (
          <button
            key={key}
            onClick={() => setMode(key)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition-colors border ${
              mode === key
                ? "bg-blue-600 text-white border-blue-600 shadow-sm"
                : "bg-white text-gray-600 border-gray-200 hover:border-blue-300 hover:text-blue-600"
            }`}
          >
            <span>{icon}</span> {mLabel}
          </button>
        ))}
      </div>

      {sorted.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-4xl mb-3">📭</p>
          <p className="text-sm">Aucun pronostic enregistré pour l&apos;instant.</p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left px-5 py-3 font-semibold text-gray-600">Joueur</th>

                  {(mode === "top5h" || mode === "top5f") && RANK_STYLES.map(({ bg, text, label: rl }) => (
                    <th key={rl} className="px-3 py-3">
                      <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full ${bg} ${text} text-xs font-bold`}>
                        {rl}
                      </span>
                    </th>
                  ))}

                  {(mode === "globesh" || mode === "globesf") && GLOBE_COLS.map(({ icon, label: gl }) => (
                    <th key={gl} className="px-4 py-3 text-left font-medium text-gray-600">
                      <span className="mr-1">{icon}</span>{gl}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {sorted.map((p) => {
                  const isMe = p.user_id === user?.user_id;
                  const cells =
                    mode === "top5h"   ? [p.top5_h.p1, p.top5_h.p2, p.top5_h.p3, p.top5_h.p4, p.top5_h.p5] :
                    mode === "top5f"   ? [p.top5_f.p1, p.top5_f.p2, p.top5_f.p3, p.top5_f.p4, p.top5_f.p5] :
                    mode === "globesh" ? [p.globes.sprint_h, p.globes.pursuit_h, p.globes.individual_h, p.globes.mass_start_h] :
                                        [p.globes.sprint_f, p.globes.pursuit_f, p.globes.individual_f, p.globes.mass_start_f];

                  return (
                    <tr key={p.user_id} className={isMe ? "bg-blue-50" : "hover:bg-gray-50"}>
                      <td className="px-5 py-3 font-medium text-gray-800">
                        <div className="flex items-center gap-2">
                          {p.username}
                          {isMe && (
                            <span className="px-1.5 py-0.5 rounded text-xs bg-blue-600 text-white font-semibold">
                              Moi
                            </span>
                          )}
                        </div>
                      </td>
                      {cells.map((id, i) => (
                        <td key={i} className="px-4 py-3 text-gray-700">
                          <AthleteCell ibuId={id} map={athMap} />
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </main>
    </SeasonGuard>
  );
}
