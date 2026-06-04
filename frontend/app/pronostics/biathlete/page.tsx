"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { pronostics, athletes, leagues, PronosticsResponse, AthleteResponse } from "@/lib/api";
import AthleteSelect from "@/components/AthleteSelect";
import Flag from "@/components/Flag";

interface Stats {
  top5: { p1: number; p2: number; p3: number; p4: number; p5: number; total: number };
  globes: { sprint: number; pursuit: number; individual: number; mass_start: number };
  myTop5Place: number | null;
  myGlobes: { sprint: boolean; pursuit: boolean; individual: boolean; mass_start: boolean };
  total: number;
}

function computeStats(data: PronosticsResponse[], ibuId: string, myUserId: string): Stats {
  const stats: Stats = {
    top5: { p1: 0, p2: 0, p3: 0, p4: 0, p5: 0, total: 0 },
    globes: { sprint: 0, pursuit: 0, individual: 0, mass_start: 0 },
    myTop5Place: null,
    myGlobes: { sprint: false, pursuit: false, individual: false, mass_start: false },
    total: data.length,
  };

  data.forEach((p) => {
    const isMe = p.user_id === myUserId;
    const top5h = [p.top5_h.p1, p.top5_h.p2, p.top5_h.p3, p.top5_h.p4, p.top5_h.p5];
    const top5f = [p.top5_f.p1, p.top5_f.p2, p.top5_f.p3, p.top5_f.p4, p.top5_f.p5];

    [...top5h, ...top5f].forEach((id, i) => {
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

function pct(n: number, total: number) {
  return total === 0 ? 0 : Math.round((n / total) * 100);
}

const RANK_STYLES = [
  { bg: "bg-yellow-400", text: "text-yellow-900", label: "1er" },
  { bg: "bg-gray-300",   text: "text-gray-700",   label: "2e"  },
  { bg: "bg-amber-600",  text: "text-amber-50",   label: "3e"  },
  { bg: "bg-gray-100",   text: "text-gray-500",   label: "4e"  },
  { bg: "bg-gray-100",   text: "text-gray-500",   label: "5e"  },
];

const GLOBE_DISCIPLINES = [
  { key: "sprint"     as const, label: "Sprint",     icon: "⚡" },
  { key: "pursuit"    as const, label: "Poursuite",  icon: "🎿" },
  { key: "individual" as const, label: "Individuel", icon: "🎯" },
  { key: "mass_start" as const, label: "Mass Start", icon: "🏁" },
];

export default function BiathletePage() {
  const { user, currentLeague } = useAuth();
  const router = useRouter();

  const [pickedAthletes, setPickedAthletes] = useState<AthleteResponse[]>([]);
  const [selected, setSelected] = useState("");
  const [data, setData] = useState<PronosticsResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) { router.push("/login"); return; }

    async function load() {
      try {
        const [all, ath] = await Promise.all([pronostics.all(), athletes.list()]);
        const athList = ath as AthleteResponse[];

        let filtered = all;
        if (currentLeague) {
          const league = await leagues.get(currentLeague.league_id, user!.token);
          const memberIds = new Set(league.members.map((m) => m.user_id));
          filtered = all.filter((p) => memberIds.has(p.user_id));
        }
        setData(filtered);

        const pickedIds = new Set<string>();
        filtered.forEach((p) => {
          [p.top5_h.p1, p.top5_h.p2, p.top5_h.p3, p.top5_h.p4, p.top5_h.p5,
           p.top5_f.p1, p.top5_f.p2, p.top5_f.p3, p.top5_f.p4, p.top5_f.p5,
           p.globes.sprint_h, p.globes.sprint_f,
           p.globes.pursuit_h, p.globes.pursuit_f,
           p.globes.individual_h, p.globes.individual_f,
           p.globes.mass_start_h, p.globes.mass_start_f,
          ].forEach((id) => { if (id) pickedIds.add(id); });
        });
        setPickedAthletes(athList.filter((a) => pickedIds.has(a.ibu_id)));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [user, currentLeague, router]);

  const stats = selected && user ? computeStats(data, selected, user.user_id) : null;
  const selectedAthlete = pickedAthletes.find((a) => a.ibu_id === selected);

  if (loading) return (
    <div className="flex justify-center items-center min-h-[60vh] text-gray-400">Chargement...</div>
  );

  return (
    <main className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">🔎 Focus Biathlète</h1>

      {/* Sélecteur */}
      <div className="max-w-sm mb-6">
        <AthleteSelect
          athletes={pickedAthletes}
          value={selected}
          onChange={setSelected}
          placeholder="Rechercher un(e) biathlète..."
        />
        {pickedAthletes.length > 0 && !selected && (
          <p className="text-xs text-gray-400 mt-1">{pickedAthletes.length} athlètes sélectionnés dans la ligue</p>
        )}
      </div>

      {!selected && (
        <div className="text-center py-16 text-gray-300">
          <p className="text-5xl mb-3">🎿</p>
          <p className="text-sm text-gray-400">Sélectionne un(e) biathlète pour voir les statistiques.</p>
        </div>
      )}

      {stats && selectedAthlete && (
        <div className="space-y-5">

          {/* Carte identité athlète */}
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5 flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3">
                <Flag nation={selectedAthlete.nation} className="w-8 h-6" />
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {selectedAthlete.family_name}{" "}
                    <span className="font-normal text-gray-500">{selectedAthlete.given_name}</span>
                  </div>
                  <p className="text-sm text-gray-400 mt-0.5">{selectedAthlete.nation}</p>
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-blue-600">{stats.top5.total + Object.values(stats.globes).reduce((a,b) => a+b, 0)}</div>
              <div className="text-xs text-gray-400">sélections au total</div>
            </div>
          </div>

          {/* Top 5 */}
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-gray-800">🏆 Top 5 Général</h2>
              <span className="text-sm text-gray-400">
                {stats.top5.total} joueur{stats.top5.total > 1 ? "s" : ""} sur {stats.total}
              </span>
            </div>

            {stats.myTop5Place && (
              <div className="mb-4 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-yellow-50 border border-yellow-200 text-yellow-700 text-sm font-medium">
                ⭐ Mon choix — {stats.myTop5Place === 1 ? "1er" : `${stats.myTop5Place}e`}
              </div>
            )}

            <div className="grid grid-cols-5 gap-2">
              {[1,2,3,4,5].map((pos) => {
                const { bg, text, label } = RANK_STYLES[pos - 1];
                const count = (stats.top5 as Record<string, number>)[`p${pos}`];
                const isMyPick = stats.myTop5Place === pos;
                return (
                  <div
                    key={pos}
                    className={`rounded-xl p-3 text-center transition-all ${
                      isMyPick
                        ? "ring-2 ring-yellow-400 ring-offset-1 bg-yellow-50"
                        : "bg-gray-50"
                    }`}
                  >
                    <div className={`mx-auto w-8 h-8 rounded-full ${bg} ${text} text-xs font-bold flex items-center justify-center mb-2`}>
                      {label}
                    </div>
                    <div className={`text-2xl font-bold ${isMyPick ? "text-yellow-600" : "text-gray-700"}`}>
                      {count}
                    </div>
                    <div className="text-xs text-gray-400 mt-0.5">{pct(count, stats.total)}%</div>
                    {isMyPick && <div className="text-xs text-yellow-500 mt-1">⭐</div>}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Globes */}
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5">
            <h2 className="font-semibold text-gray-800 mb-4">🌍 Globes de Cristal</h2>
            <div className="space-y-4">
              {GLOBE_DISCIPLINES.map(({ key, label, icon }) => {
                const count = stats.globes[key];
                const isMyPick = stats.myGlobes[key];
                const p = pct(count, stats.total);
                return (
                  <div key={key} className={`p-3 rounded-xl ${isMyPick ? "bg-yellow-50 border border-yellow-200" : "bg-gray-50"}`}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{icon}</span>
                        <span className={`text-sm font-medium ${isMyPick ? "text-yellow-700" : "text-gray-700"}`}>
                          {label}
                        </span>
                        {isMyPick && (
                          <span className="px-2 py-0.5 rounded-full bg-yellow-400 text-yellow-900 text-xs font-bold">
                            ⭐ Mon choix
                          </span>
                        )}
                      </div>
                      <span className="text-sm font-semibold text-gray-600">
                        {count}/{stats.total} <span className="text-gray-400 font-normal">({p}%)</span>
                      </span>
                    </div>
                    <div className="h-2.5 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${isMyPick ? "bg-yellow-400" : "bg-blue-400"}`}
                        style={{ width: `${p}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

        </div>
      )}
    </main>
  );
}
