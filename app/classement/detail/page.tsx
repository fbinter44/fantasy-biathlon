"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import {
  score, leagues, ScoreBreakdown, AthleteScoreDetail,
  GlobeScoreDetail, RaceScoreDetail,
} from "@/lib/api";
import Flag from "@/components/Flag";

// ── Helpers ───────────────────────────────────────────────

const RANK_MEDALS = ["🥇", "🥈", "🥉", "4e", "5e"];
const GENDER_LABEL: Record<string, string> = { Men: "H", Women: "F" };

function pts(n: number, colored = true) {
  if (n === 0) return <span className="text-gray-300">0 pt</span>;
  return <span className={colored ? "text-blue-700 font-semibold" : ""}>{n} pts</span>;
}

// ── Bloc résumé ───────────────────────────────────────────

function SummaryBar({ data }: { data: ScoreBreakdown }) {
  const categories = [
    { label: "Hommes",  value: data.men_points,    color: "bg-blue-500" },
    { label: "Femmes",  value: data.women_points,   color: "bg-pink-400" },
    { label: "Globes",  value: data.globe_points,   color: "bg-emerald-500" },
    { label: "Courses", value: data.race_points,    color: "bg-amber-400" },
  ];
  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5 mb-6">
      <div className="flex items-baseline gap-3 mb-4">
        <span className="text-3xl font-bold text-blue-700">{data.total_points}</span>
        <span className="text-gray-400 text-sm">points au total</span>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {categories.map((c) => (
          <div key={c.label} className="text-center">
            <div className={`h-1.5 rounded-full mb-1.5 ${c.color}`} />
            <p className="text-lg font-bold text-gray-800">{c.value}</p>
            <p className="text-xs text-gray-400">{c.label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Bloc athlètes saison ──────────────────────────────────

function AthleteTable({ athletes, title }: { athletes: AthleteScoreDetail[]; title: string }) {
  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden mb-4">
      <div className="px-5 py-3 bg-gray-50 border-b border-gray-100 font-semibold text-gray-800 text-sm">
        {title}
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-xs text-gray-400 border-b border-gray-100">
            <th className="text-left px-4 py-2">Rang prédit</th>
            <th className="text-left px-4 py-2">Athlète</th>
            <th className="text-center px-4 py-2">Rang réel</th>
            <th className="text-right px-4 py-2">Points</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50">
          {athletes.map((a) => (
            <tr key={a.ibu_id} className={a.points > 0 ? "bg-blue-50/40" : ""}>
              <td className="px-4 py-2.5 text-gray-500">
                {RANK_MEDALS[a.predicted_rank - 1] ?? a.predicted_rank}
              </td>
              <td className="px-4 py-2.5">
                <span className="inline-flex items-center gap-2">
                  <Flag nation={a.nation} />
                  <span className="text-gray-800">{a.name}</span>
                </span>
              </td>
              <td className="px-4 py-2.5 text-center">
                {a.actual_rank != null ? (
                  <span className={a.exact_rank_bonus ? "text-green-600 font-bold" : "text-gray-600"}>
                    {a.actual_rank}
                    {a.exact_rank_bonus && " ⭐"}
                  </span>
                ) : (
                  <span className="text-gray-300">hors top</span>
                )}
              </td>
              <td className="px-4 py-2.5 text-right">
                {pts(a.points)}
                {a.exact_rank_bonus && (
                  <span className="ml-1 text-xs text-green-600">(+50 bonus)</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Bloc globes ───────────────────────────────────────────

function GlobeTable({ globes }: { globes: GlobeScoreDetail[] }) {
  const byDisc = globes.reduce<Record<string, { Men?: GlobeScoreDetail; Women?: GlobeScoreDetail }>>(
    (acc, g) => {
      if (!acc[g.discipline]) acc[g.discipline] = {};
      acc[g.discipline][g.gender as "Men" | "Women"] = g;
      return acc;
    }, {}
  );

  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden mb-4">
      <div className="px-5 py-3 bg-gray-50 border-b border-gray-100 font-semibold text-gray-800 text-sm">
        🌍 Globes de cristal
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-xs text-gray-400 border-b border-gray-100">
            <th className="text-left px-4 py-2">Discipline</th>
            <th className="text-left px-4 py-2">H / F</th>
            <th className="text-left px-4 py-2">Ton pronostic</th>
            <th className="text-left px-4 py-2">Leader actuel</th>
            <th className="text-right px-4 py-2">Points</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50">
          {Object.entries(byDisc).flatMap(([disc, genders]) =>
            (["Men", "Women"] as const).map((g) => {
              const row = genders[g];
              if (!row) return null;
              return (
                <tr key={`${disc}-${g}`} className={row.correct ? "bg-green-50/40" : ""}>
                  <td className="px-4 py-2.5 text-gray-600">{row.discipline_display}</td>
                  <td className="px-4 py-2.5 text-gray-400">{GENDER_LABEL[g]}</td>
                  <td className="px-4 py-2.5 text-gray-800">{row.predicted_name}</td>
                  <td className="px-4 py-2.5">
                    {row.actual_leader_name ?? <span className="text-gray-300">—</span>}
                    {row.correct && " ✅"}
                  </td>
                  <td className="px-4 py-2.5 text-right">{pts(row.points)}</td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}

// ── Bloc courses ──────────────────────────────────────────

function RaceTable({ races }: { races: RaceScoreDetail[] }) {
  const correct = races.filter((r) => r.correct);

  if (correct.length === 0)
    return (
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 text-center text-sm text-gray-400 mb-4">
        Tu n&apos;as pas eu de bons pronostics sur les courses passées
      </div>
    );

  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden mb-4">
      <div className="px-5 py-3 bg-gray-50 border-b border-gray-100 font-semibold text-gray-800 text-sm">
        🎯 Courses gagnées ({correct.length})
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-xs text-gray-400 border-b border-gray-100">
            <th className="text-left px-4 py-2">Course</th>
            <th className="text-left px-4 py-2">Vainqueur prédit ✅</th>
            <th className="text-right px-4 py-2">Points</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50">
          {correct.map((r) => (
            <tr key={r.race_id} className="bg-green-50/40">
              <td className="px-4 py-2.5">
                <p className="text-gray-800 font-medium">{r.location}</p>
                <p className="text-xs text-gray-400">
                  {r.discipline_display} {GENDER_LABEL[r.gender] ?? r.gender} · {new Date(r.date).toLocaleDateString("fr-FR", { day: "numeric", month: "short" })}
                </p>
              </td>
              <td className="px-4 py-2.5 text-green-700 font-medium">{r.winner_name} ✅</td>
              <td className="px-4 py-2.5 text-right">{pts(r.points)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Page principale (inner) ───────────────────────────────

function DetailScoreContent() {
  const { user, currentLeague } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [members, setMembers] = useState<{ user_id: string; username: string }[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [breakdown, setBreakdown] = useState<ScoreBreakdown | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Chargement des membres de la ligue
  useEffect(() => {
    if (!user) { router.push("/login"); return; }
    if (!currentLeague) return;
    leagues.get(currentLeague.league_id, user.token).then((l) => {
      setMembers(l.members);
      // Pré-sélection via URL param ?userId=... (depuis la page évolution)
      const urlUserId = searchParams?.get("userId");
      const isValidMember = urlUserId && l.members.some((m) => m.user_id === urlUserId);
      setSelectedId(isValidMember ? urlUserId! : user.user_id);
    });
  }, [user, currentLeague, router, searchParams]);

  // Chargement du score quand le joueur sélectionné change
  useEffect(() => {
    if (!user || !selectedId) return;
    setLoading(true);
    setError("");
    setBreakdown(null);
    score.get(selectedId, user.token)
      .then(setBreakdown)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Erreur"))
      .finally(() => setLoading(false));
  }, [user, selectedId]);

  if (!user) return null;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-1">
        <h1 className="text-2xl font-bold text-gray-900">🔍 Détail des scores</h1>
        <button
          onClick={() => router.back()}
          className="ml-auto text-sm text-gray-400 hover:text-gray-700 transition-colors"
        >
          ← Retour
        </button>
      </div>
      <p className="text-sm text-gray-500 mb-6">Décomposition point par point</p>

      {/* Sélecteur de joueur */}
      {members.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-6">
          {members.map((m) => (
            <button
              key={m.user_id}
              onClick={() => setSelectedId(m.user_id)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                selectedId === m.user_id
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {m.username}
              {m.user_id === user.user_id && " 👤"}
            </button>
          ))}
        </div>
      )}

      {loading && (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-40 bg-gray-100 rounded-2xl animate-pulse" />
          ))}
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-700">{error}</div>
      )}

      {breakdown && !loading && (
        <>
          <SummaryBar data={breakdown} />

          <h2 className="text-base font-semibold text-gray-700 mb-3">🏔️ Pronos Saison</h2>
          <AthleteTable athletes={breakdown.men_athletes} title="Hommes — Top 5 général" />
          <AthleteTable athletes={breakdown.women_athletes} title="Femmes — Top 5 général" />

          {breakdown.globes.length > 0 && <GlobeTable globes={breakdown.globes} />}

          <h2 className="text-base font-semibold text-gray-700 mb-3 mt-6">🎯 Pronos Course par course</h2>
          <RaceTable races={breakdown.races} />
        </>
      )}
    </div>
  );
}

// ── Wrapper Suspense (requis pour useSearchParams en App Router) ───────────────

export default function DetailScorePage() {
  return (
    <Suspense fallback={<div className="flex justify-center items-center min-h-[60vh] text-gray-400">Chargement…</div>}>
      <DetailScoreContent />
    </Suspense>
  );
}
