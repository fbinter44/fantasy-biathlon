"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import {
  standings, pronostics,
  StandingsResponse, AthleteStanding, PronosticsResponse, SeasonProgress, GlobeWinners,
} from "@/lib/api";
import { useSeason } from "@/context/SeasonContext";
import SeasonGuard from "@/components/SeasonGuard";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import Flag from "@/components/Flag";

const DISCIPLINES = [
  { key: "general", label: "Classement Général" },
  { key: "sprint", label: "Sprint" },
  { key: "pursuit", label: "Poursuite" },
  { key: "individual", label: "Individuel" },
  { key: "mass_start", label: "Mass Start" },
] as const;

type DisciplineKey = typeof DISCIPLINES[number]["key"];

function getPredictedIds(
  pronos: PronosticsResponse | null,
  discipline: DisciplineKey,
  gender: "Men" | "Women"
): Set<string> {
  if (!pronos) return new Set();
  if (discipline === "general") {
    const top5 = gender === "Men" ? pronos.top5_h : pronos.top5_f;
    return new Set(Object.values(top5).filter(Boolean));
  }
  const key = `${discipline}_${gender === "Men" ? "h" : "f"}` as keyof GlobeWinners;
  const id = pronos.globes[key];
  return id ? new Set([id]) : new Set();
}

function getDisciplineAthletes(
  standingsData: StandingsResponse | null,
  discipline: DisciplineKey
): AthleteStanding[] {
  if (!standingsData) return [];
  const disc = standingsData.disciplines.find((d) => d.discipline === discipline);
  return disc?.athletes ?? [];
}

function getProgress(progressData: SeasonProgress[], discipline: DisciplineKey) {
  return progressData.find((p) => p.discipline === discipline) ?? null;
}

function AthleteRow({ a, isPicked, dimmed }: { a: AthleteStanding; isPicked: boolean; dimmed: boolean }) {
  return (
    <tr className={`${dimmed ? "opacity-40" : ""} ${isPicked && !dimmed ? "bg-yellow-50" : "hover:bg-gray-50"}`}>
      <td className="px-3 py-2 text-gray-400">{a.rank}</td>
      <td className="px-3 py-2">
        <span className="inline-flex items-center gap-1.5">
          <Flag nation={a.nation} />
          {a.name}
          {isPicked && <span className="text-xs text-yellow-600">★</span>}
        </span>
      </td>
      <td className="px-3 py-2 text-right font-medium">{a.points}</td>
    </tr>
  );
}

function StandingsTable({
  athletes,
  predictedIds,
  title,
  progress,
}: {
  athletes: AthleteStanding[];
  predictedIds: Set<string>;
  title: string;
  progress: SeasonProgress | null;
}) {
  const [showMore, setShowMore] = useState(false);
  const top10 = athletes.slice(0, 10);
  const rest = athletes.slice(10);

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-gray-700">{title}</h3>
        {progress && (
          <span className="text-xs text-gray-400">
            {progress.races_done}/{progress.races_total} courses
          </span>
        )}
      </div>

      <div className="rounded-xl border border-gray-200 overflow-hidden mb-4">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-3 py-2 text-gray-500 font-medium w-8">#</th>
              <th className="text-left px-3 py-2 text-gray-500 font-medium">Athlète</th>
              <th className="text-right px-3 py-2 text-gray-500 font-medium">Points</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {top10.map((a) => (
              <AthleteRow key={a.ibu_id} a={a} isPicked={predictedIds.has(a.ibu_id)} dimmed={false} />
            ))}
            {showMore && rest.map((a) => (
              <AthleteRow key={a.ibu_id} a={a} isPicked={predictedIds.has(a.ibu_id)} dimmed={true} />
            ))}
          </tbody>
        </table>

        {rest.length > 0 && (
          <button
            onClick={() => setShowMore((v) => !v)}
            className="w-full py-2 text-xs text-gray-400 hover:text-gray-600 hover:bg-gray-50 border-t border-gray-100 transition-colors"
          >
            {showMore
              ? "▲ Masquer les places 11–20"
              : `▼ Voir les places 11–${10 + rest.length} (hors top 10)`}
          </button>
        )}
      </div>

      {top10.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 mb-2">Écarts de points — Top 10</p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={top10} margin={{ top: 4, right: 8, left: 0, bottom: 40 }}>
              <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-35} textAnchor="end" interval={0} />
              <YAxis tick={{ fontSize: 10 }} width={40} />
              <Tooltip formatter={(v) => [`${v} pts`, "Points"]} />
              <Bar dataKey="points" radius={[3, 3, 0, 0]}>
                {top10.map((a) => (
                  <Cell key={a.ibu_id} fill={predictedIds.has(a.ibu_id) ? "#f59e0b" : "#3b82f6"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

export default function ResultatsPage() {
  const { user } = useAuth();
  const { selected } = useSeason();
  const router = useRouter();

  const [menSt, setMenSt] = useState<StandingsResponse | null>(null);
  const [womenSt, setWomenSt] = useState<StandingsResponse | null>(null);
  const [menProg, setMenProg] = useState<SeasonProgress[]>([]);
  const [womenProg, setWomenProg] = useState<SeasonProgress[]>([]);
  const [myPronos, setMyPronos] = useState<PronosticsResponse | null>(null);
  const [discipline, setDiscipline] = useState<DisciplineKey>("general");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) { router.push("/login"); return; }

    async function load() {
      const [men, women, progM, progW, pron] = await Promise.allSettled([
        standings.get("Men", selected.code),
        standings.get("Women", selected.code),
        standings.progress("Men", selected.code),
        standings.progress("Women", selected.code),
        pronostics.me(user!.token, selected.code),
      ]);

      if (men.status === "fulfilled") setMenSt(men.value);
      if (women.status === "fulfilled") setWomenSt(women.value);
      if (progM.status === "fulfilled") setMenProg(progM.value);
      if (progW.status === "fulfilled") setWomenProg(progW.value);
      if (pron.status === "fulfilled") setMyPronos(pron.value);
      setLoading(false);
    }
    load();
  }, [user, router, selected.code]);

  const menAthletes = getDisciplineAthletes(menSt, discipline);
  const womenAthletes = getDisciplineAthletes(womenSt, discipline);
  const menPredicted = getPredictedIds(myPronos, discipline, "Men");
  const womenPredicted = getPredictedIds(myPronos, discipline, "Women");
  const menProgress = getProgress(menProg, discipline);
  const womenProgress = getProgress(womenProg, discipline);

  if (loading) return (
    <div className="flex justify-center items-center min-h-[60vh] text-gray-400">
      Chargement des résultats IBU...
    </div>
  );

  return (
    <SeasonGuard>
    <main className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">📊 Résultats Officiels IBU</h1>

      {/* Tabs disciplines */}
      <div className="flex flex-wrap gap-2 mb-6">
        {DISCIPLINES.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setDiscipline(key)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium border transition-colors ${
              discipline === key
                ? "bg-blue-600 text-white border-blue-600"
                : "bg-blue-50 text-blue-600 border-blue-200 hover:bg-blue-100"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {myPronos && (
        <p className="text-xs text-gray-400 mb-4">
          ★ = ton pronostic
        </p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <StandingsTable
          athletes={menAthletes}
          predictedIds={menPredicted}
          title="🧔 Hommes"
          progress={menProgress}
        />
        <StandingsTable
          athletes={womenAthletes}
          predictedIds={womenPredicted}
          title="👩 Femmes"
          progress={womenProgress}
        />
      </div>
    </main>
    </SeasonGuard>
  );
}
