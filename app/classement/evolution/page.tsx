"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { classement, leagues } from "@/lib/api";
import { buildChartData, type ChartRow } from "@/lib/utils";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, Legend,
  ResponsiveContainer, CartesianGrid,
} from "recharts";

const COLORS = [
  "#3b82f6", "#ec4899", "#10b981", "#f59e0b",
  "#8b5cf6", "#ef4444", "#06b6d4", "#84cc16",
];

export default function EvolutionPage() {
  const { user, currentLeague } = useAuth();
  const router = useRouter();

  const [chartData, setChartData] = useState<ChartRow[]>([]);
  const [players, setPlayers] = useState<string[]>([]);
  const [myUsername, setMyUsername] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) { router.push("/login"); return; }

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

        const { chartData: cd, players: pl } = buildChartData(evo, ids);
        setChartData(cd);
        setPlayers(pl);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [user, currentLeague, router]);

  // Pivot table
  const venues = chartData.map((r) => r.venue as string);
  const pivot = players.map((username) => {
    const row: Record<string, string | number> = { Joueur: username };
    chartData.forEach((r) => { row[r.venue as string] = r[username] ?? 0; });
    return row;
  }).sort((a, b) => {
    const lastVenue = venues[venues.length - 1];
    return (b[lastVenue] as number) - (a[lastVenue] as number);
  });

  if (loading) return (
    <div className="flex justify-center items-center min-h-[60vh] text-gray-400">
      Calcul de l&apos;évolution... (peut prendre quelques secondes)
    </div>
  );

  if (chartData.length === 0) return (
    <main className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">📉 Évolution du classement</h1>
      <p className="text-gray-500 text-sm">Aucune donnée disponible pour l&apos;instant.</p>
    </main>
  );

  return (
    <main className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">📉 Évolution du classement</h1>
      <p className="text-gray-500 text-sm mb-3">
        Évolution des points fantasy après chaque week-end de compétition.
      </p>
      <div className="mb-6 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-800 text-sm">
        ⚠️ Cette page n&apos;est actualisée qu&apos;à la fin de chaque week-end de compétitions.
      </div>

      {/* Line chart */}
      <section className="mb-10">
        <h2 className="text-lg font-semibold text-gray-700 mb-3">📈 Évolution des points</h2>
        <div className="bg-white border border-gray-200 rounded-xl p-4">
          <ResponsiveContainer width="100%" height={420}>
            <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="venue" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
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
                    opacity={isMe ? 1 : 0.6}
                  />
                );
              })}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* Tableau pivot */}
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
    </main>
  );
}
