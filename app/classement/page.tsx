"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { classement, leagues, PlayerPoints } from "@/lib/api";
import type { VenueEvolution } from "@/lib/api";
import { buildChartData } from "@/lib/utils";
import type { ChartRow } from "@/lib/utils";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend,
  ResponsiveContainer, LabelList,
  LineChart, Line, CartesianGrid,
} from "recharts";

// ─── Types ───────────────────────────────────────────────────────────────────

type View = "classement" | "evolution";

// ─── Constantes ──────────────────────────────────────────────────────────────

const MEDALS = ["🥇", "🥈", "🥉"];
const COLORS = ["#3b82f6","#ec4899","#10b981","#f59e0b","#8b5cf6","#ef4444","#06b6d4","#84cc16"];

// ─── Tooltip personnalisé (évolution) ────────────────────────────────────────

interface EvoPayloadEntry { name?: string; value?: number; color?: string; }
interface EvoTooltipProps {
  active?: boolean;
  payload?: EvoPayloadEntry[];
  label?: string;
  fullEvolution: VenueEvolution[];
}

function EvoTooltip({ active, payload, label, fullEvolution }: EvoTooltipProps) {
  if (!active || !payload?.length || !label) return null;

  const venueIdx = fullEvolution.findIndex((v) => v.name === label);
  if (venueIdx < 0) return null;
  const venue = fullEvolution[venueIdx];
  const prevVenue = venueIdx > 0 ? fullEvolution[venueIdx - 1] : null;

  const sorted = [...payload].sort((a, b) => (b.value ?? 0) - (a.value ?? 0));

  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-lg p-4 min-w-[220px] text-sm">
      <p className="font-semibold text-gray-800 mb-3">{label}</p>
      {sorted.map((entry) => {
        const username = entry.name ?? "";
        const player = venue.players.find((p) => p.username === username);
        const prevPlayer = prevVenue?.players.find((p) => p.username === username);
        if (!player) return null;

        const delta = prevPlayer != null ? player.total_points - prevPlayer.total_points : null;
        const parts: string[] = [];
        if (prevPlayer != null) {
          const dH = player.men_points - prevPlayer.men_points;
          const dF = player.women_points - prevPlayer.women_points;
          const dG = player.globe_points - prevPlayer.globe_points;
          const dR = player.race_points - prevPlayer.race_points;
          if (dH !== 0) parts.push(`H ${dH > 0 ? "+" : ""}${dH}`);
          if (dF !== 0) parts.push(`F ${dF > 0 ? "+" : ""}${dF}`);
          if (dG !== 0) parts.push(`Globes ${dG > 0 ? "+" : ""}${dG}`);
          if (dR !== 0) parts.push(`Courses ${dR > 0 ? "+" : ""}${dR}`);
        }

        return (
          <div key={username} className="mb-2.5">
            <div className="flex items-center gap-2">
              <span className="inline-block w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: entry.color }} />
              <span className="font-medium text-gray-800 truncate">{username}</span>
              <span className="ml-auto font-bold text-blue-700 shrink-0">{player.total_points} pts</span>
            </div>
            {delta != null && (
              <p className="ml-4 mt-0.5 text-xs text-gray-500">
                {delta > 0 ? `+${delta}` : delta < 0 ? `${delta}` : "stable"} ce week-end
                {parts.length > 0 && (
                  <span className="text-gray-400 ml-1">({parts.join(" · ")})</span>
                )}
              </p>
            )}
          </div>
        );
      })}
      <p className="text-xs text-gray-400 border-t border-gray-100 pt-2 mt-1">
        Cliquez sur la légende pour voir le détail 🔍
      </p>
    </div>
  );
}

// ─── Composants ──────────────────────────────────────────────────────────────

function PodiumCard({ player }: { player: PlayerPoints }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 text-center shadow-sm">
      <div className="text-3xl mb-1">{MEDALS[player.rank! - 1]}</div>
      <div className="font-bold text-gray-900">{player.username}</div>
      <div className="text-2xl font-bold text-blue-600 mt-1">{player.total_points} pts</div>
      <div className="text-xs text-gray-400 mt-1">
        H: {player.men_points} | F: {player.women_points} | Globes: {player.globe_points} | Courses: {player.race_points}
      </div>
    </div>
  );
}

// ─── Page principale ──────────────────────────────────────────────────────────

export default function ClassementSkiClubPage() {
  const { user, currentLeague } = useAuth();
  const router = useRouter();

  const [view, setView] = useState<View>("classement");

  // Données classement
  const [rankData, setRankData] = useState<PlayerPoints[]>([]);
  const [rankLoading, setRankLoading] = useState(true);

  // Données évolution (chargées à la demande)
  const [chartData, setChartData] = useState<ChartRow[]>([]);
  const [players, setPlayers] = useState<string[]>([]);
  const [myUsername, setMyUsername] = useState("");
  const [fullEvolution, setFullEvolution] = useState<VenueEvolution[]>([]);
  const [usernameToUserId, setUsernameToUserId] = useState<Map<string, string>>(new Map());
  const [evoLoading, setEvoLoading] = useState(false);
  const [evoLoaded, setEvoLoaded] = useState(false);

  // Chargement du classement
  useEffect(() => {
    if (!user) { router.push("/login"); return; }
    async function load() {
      try {
        const result = currentLeague
          ? await classement.league(currentLeague.league_id, user!.token)
          : await classement.global();
        setRankData(result);
      } finally {
        setRankLoading(false);
      }
    }
    load();
  }, [user, currentLeague, router]);

  // Chargement de l'évolution (uniquement quand l'onglet est ouvert)
  useEffect(() => {
    if (view !== "evolution" || evoLoaded || !user) return;
    setEvoLoading(true);
    async function load() {
      try {
        const [evo, league] = await Promise.all([
          classement.evolution(),
          currentLeague ? leagues.get(currentLeague.league_id, user!.token) : Promise.resolve(null),
        ]);
        const ids = league ? new Set(league.members.map((m) => m.user_id)) : null;
        setMyUsername(
          evo[0]?.players.find((p) => p.user_id === user!.user_id)?.username ?? user!.username
        );
        const { chartData: cd, players: pl, usernameToUserId: u2id } = buildChartData(evo, ids);
        setChartData(cd);
        setPlayers(pl);
        setFullEvolution(evo);
        setUsernameToUserId(u2id);
        setEvoLoaded(true);
      } finally {
        setEvoLoading(false);
      }
    }
    load();
  }, [view, evoLoaded, user, currentLeague]);

  const venues = chartData.map((r) => r.venue as string);
  const pivot = players.map((username) => {
    const row: Record<string, string | number> = { Joueur: username };
    chartData.forEach((r) => { row[r.venue as string] = r[username] ?? 0; });
    return row;
  }).sort((a, b) => {
    const last = venues[venues.length - 1];
    return (b[last] as number) - (a[last] as number);
  });

  if (rankLoading) return (
    <div className="flex justify-center items-center min-h-[60vh] text-gray-400">Chargement...</div>
  );

  return (
    <main className="max-w-7xl mx-auto px-4 py-8">
      {/* Titre + toggle */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-8">
        <h1 className="text-2xl font-bold text-gray-900">🏆 Classement du Ski Club</h1>
        <div className="flex bg-gray-100 p-1 rounded-xl gap-1">
          <button
            onClick={() => setView("classement")}
            className={`px-5 py-2 rounded-lg text-sm font-medium transition-colors ${
              view === "classement"
                ? "bg-white shadow text-blue-600"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            🏆 Résultats
          </button>
          <button
            onClick={() => setView("evolution")}
            className={`px-5 py-2 rounded-lg text-sm font-medium transition-colors ${
              view === "evolution"
                ? "bg-white shadow text-blue-600"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            📉 Évolution
          </button>
        </div>
      </div>

      {/* ── Vue Classement ── */}
      {view === "classement" && (
        <>
          {rankData.slice(0, 3).length > 0 && (
            <section className="mb-8">
              <h2 className="text-lg font-semibold text-gray-700 mb-3">🥇 Top 3</h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {rankData.slice(0, 3).map((p) => <PodiumCard key={p.user_id} player={p} />)}
              </div>
            </section>
          )}

          <section className="mb-10">
            <h2 className="text-lg font-semibold text-gray-700 mb-3">📋 Tableau complet</h2>
            <div className="overflow-x-auto rounded-xl border border-gray-200">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    {["#", "Joueur", "Total", "Hommes", "Femmes", "Globes", "Courses"].map((h) => (
                      <th key={h} className="text-left px-4 py-3 font-medium text-gray-600">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {rankData.map((p) => {
                    const isMe = p.user_id === user?.user_id;
                    return (
                      <tr key={p.user_id} className={isMe ? "bg-blue-50 font-medium" : "hover:bg-gray-50"}>
                        <td className="px-4 py-3 text-gray-400">{p.rank}</td>
                        <td className="px-4 py-3">{p.username}{isMe && " 👤"}</td>
                        <td className="px-4 py-3 font-bold text-blue-700">{p.total_points}</td>
                        <td className="px-4 py-3">{p.men_points}</td>
                        <td className="px-4 py-3">{p.women_points}</td>
                        <td className="px-4 py-3">{p.globe_points}</td>
                        <td className="px-4 py-3">{p.race_points}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>

          <section className="mb-10">
            <h2 className="text-lg font-semibold text-gray-700 mb-3">📊 Répartition des points</h2>
            <div className="bg-white border border-gray-200 rounded-xl p-4">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={rankData} margin={{ top: 20, right: 20, left: 0, bottom: 0 }}>
                  <XAxis dataKey="username" tick={{ fontSize: 13 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="total_points" name="Total" fill="#3b82f6" radius={[4,4,0,0]}>
                    <LabelList dataKey="total_points" position="top" style={{ fontSize: 12 }} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="mb-10">
            <h2 className="text-lg font-semibold text-gray-700 mb-3">👥 Points Hommes vs Femmes</h2>
            <div className="bg-white border border-gray-200 rounded-xl p-4">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={rankData} margin={{ top: 20, right: 20, left: 0, bottom: 0 }}>
                  <XAxis dataKey="username" tick={{ fontSize: 13 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip /><Legend />
                  <Bar dataKey="men_points" name="Hommes" fill="#3b82f6" radius={[4,4,0,0]} />
                  <Bar dataKey="women_points" name="Femmes" fill="#ec4899" radius={[4,4,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="mb-6">
            <h2 className="text-lg font-semibold text-gray-700 mb-3">🌍 Points Globes de cristal</h2>
            <div className="bg-white border border-gray-200 rounded-xl p-4">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={rankData} margin={{ top: 20, right: 20, left: 0, bottom: 0 }}>
                  <XAxis dataKey="username" tick={{ fontSize: 13 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="globe_points" name="Globes" fill="#10b981" radius={[4,4,0,0]}>
                    <LabelList dataKey="globe_points" position="top" style={{ fontSize: 12 }} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="mb-6">
            <h2 className="text-lg font-semibold text-gray-700 mb-3">🎯 Points Courses</h2>
            <div className="bg-white border border-gray-200 rounded-xl p-4">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={rankData} margin={{ top: 20, right: 20, left: 0, bottom: 0 }}>
                  <XAxis dataKey="username" tick={{ fontSize: 13 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="race_points" name="Courses" fill="#f59e0b" radius={[4,4,0,0]}>
                    <LabelList dataKey="race_points" position="top" style={{ fontSize: 12 }} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>
        </>
      )}

      {/* ── Vue Évolution ── */}
      {view === "evolution" && (
        <>
          {evoLoading ? (
            <div className="flex justify-center items-center min-h-[40vh] text-gray-400">
              Calcul de l&apos;évolution… (peut prendre quelques secondes)
            </div>
          ) : chartData.length === 0 ? (
            <p className="text-gray-500 text-sm">Aucune donnée disponible pour l&apos;instant.</p>
          ) : (
            <>
              <div className="mb-6 p-3 bg-yellow-50 border border-yellow-200 rounded-xl text-yellow-800 text-sm">
                ⚠️ Cette vue n&apos;est actualisée qu&apos;à la fin de chaque week-end de compétitions.
              </div>

              <section className="mb-10">
                <h2 className="text-lg font-semibold text-gray-700 mb-3">📈 Évolution des points</h2>
                <p className="text-xs text-gray-400 mb-2">Survolez un point pour voir le détail du week-end · Cliquez sur un nom dans la légende pour voir son score détaillé</p>
                <div className="bg-white border border-gray-200 rounded-xl p-4">
                  <ResponsiveContainer width="100%" height={420}>
                    <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="venue" tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip
                        content={(props: any) => (
                          <EvoTooltip
                            active={props.active}
                            payload={props.payload}
                            label={props.label}
                            fullEvolution={fullEvolution}
                          />
                        )}
                      />
                      <Legend
                        wrapperStyle={{ cursor: "pointer" }}
                        onClick={(data) => {
                          const username = data.dataKey as string;
                          const userId = usernameToUserId.get(username);
                          if (userId) router.push(`/classement/detail?userId=${userId}`);
                        }}
                      />
                      {players.map((username, i) => {
                        const isMe = username === myUsername;
                        return (
                          <Line
                            key={username}
                            type="monotone"
                            dataKey={username}
                            stroke={isMe ? "#ef4444" : COLORS[i % COLORS.length]}
                            strokeWidth={isMe ? 3 : 1.5}
                            dot={false}
                            activeDot={{
                              r: 5,
                              cursor: "pointer",
                              onClick: () => {
                                const userId = usernameToUserId.get(username);
                                if (userId) router.push(`/classement/detail?userId=${userId}`);
                              },
                            }}
                            opacity={isMe ? 1 : 0.6}
                          />
                        );
                      })}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </section>

              <section>
                <h2 className="text-lg font-semibold text-gray-700 mb-3">📋 Détail par week-end</h2>
                <div className="overflow-x-auto rounded-xl border border-gray-200">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="text-left px-4 py-3 font-medium text-gray-600">Joueur</th>
                        {venues.map((v) => (
                          <th key={v} className="text-left px-4 py-3 font-medium text-gray-600">{v}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {pivot.map((row) => {
                        const isMe = row["Joueur"] === myUsername;
                        return (
                          <tr key={row["Joueur"]} className={isMe ? "bg-blue-50 font-medium" : "hover:bg-gray-50"}>
                            <td className="px-4 py-3">{row["Joueur"]}{isMe && " 👤"}</td>
                            {venues.map((v) => (
                              <td key={v} className="px-4 py-3">{row[v] ?? 0}</td>
                            ))}
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          )}
        </>
      )}
    </main>
  );
}
