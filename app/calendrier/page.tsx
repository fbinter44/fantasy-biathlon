"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import Link from "next/link";
import { calendar, racePronostics, VenueInfo, RaceInfo, RaceResult } from "@/lib/api";
import Flag from "@/components/Flag";

// ── Helpers ──────────────────────────────────────────────

const DISCIPLINE_COLORS: Record<string, string> = {
  sprint:     "bg-blue-100 text-blue-700",
  pursuit:    "bg-green-100 text-green-700",
  individual: "bg-orange-100 text-orange-700",
  mass_start: "bg-purple-100 text-purple-700",
};

const GENDER_LABEL: Record<string, string> = {
  Men:   "H",
  Women: "F",
};

const GENDER_COLORS: Record<string, string> = {
  Men:   "bg-sky-50 text-sky-600",
  Women: "bg-pink-50 text-pink-600",
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("fr-FR", {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
}

function formatDateRange(start: string, end: string): string {
  const s = new Date(start);
  const e = new Date(end);
  const opts: Intl.DateTimeFormatOptions = { day: "numeric", month: "long", year: "numeric" };
  if (start === end) return s.toLocaleDateString("fr-FR", opts);
  if (s.getMonth() === e.getMonth())
    return `${s.getDate()}–${e.toLocaleDateString("fr-FR", opts)}`;
  return `${s.toLocaleDateString("fr-FR", { day: "numeric", month: "long" })} – ${e.toLocaleDateString("fr-FR", opts)}`;
}

function isOngoing(start: string, end: string): boolean {
  const now = new Date();
  return now >= new Date(start) && now <= new Date(end + "T23:59:59");
}

// ── Composant résultats ───────────────────────────────────

function ResultsTable({
  results,
  predictedIbuId,
}: {
  results: RaceResult[];
  predictedIbuId: string;
}) {
  if (results.length === 0)
    return <p className="text-sm text-gray-400 py-3 text-center">Aucun résultat disponible.</p>;

  const winner = results.find((r) => String(r.rank) === "1")?.ibu_id;
  const correct = predictedIbuId && predictedIbuId === winner;

  return (
    <div className="overflow-x-auto mt-1">
      {predictedIbuId && (
        <p className={`text-xs mb-2 ${correct ? "text-green-600 font-medium" : "text-gray-400"}`}>
          {correct ? "✅ Bon pronostic ! +10 pts" : "❌ Ton pronostic n'était pas le vainqueur"}
        </p>
      )}
      <table className="w-full text-sm">
        <thead>
          <tr className="text-xs text-gray-400 border-b border-gray-100">
            <th className="text-right pr-3 py-2 font-medium w-10">Rang</th>
            <th className="text-left py-2 font-medium">Athlète</th>
            <th className="text-right pl-3 py-2 font-medium w-16">Points</th>
          </tr>
        </thead>
        <tbody>
          {results.map((r) => {
            const isPredicted = predictedIbuId && r.ibu_id === predictedIbuId;
            return (
              <tr
                key={r.rank}
                className={`border-b border-gray-50 transition-colors ${
                  isPredicted
                    ? "bg-yellow-50 hover:bg-yellow-100"
                    : "hover:bg-gray-50"
                }`}
              >
                <td className="text-right pr-3 py-1.5 text-gray-400 font-mono text-xs">
                  {r.rank}
                </td>
                <td className="py-1.5">
                  <span className="inline-flex items-center gap-2">
                    <Flag nation={r.nation} />
                    <span className={isPredicted ? "font-semibold text-yellow-800" : "text-gray-800"}>
                      {r.name}
                    </span>
                    {isPredicted && <span className="text-xs text-yellow-600">★ ton pronostic</span>}
                  </span>
                </td>
                <td className="text-right pl-3 py-1.5 font-medium text-gray-700">
                  {r.points > 0 ? r.points : "–"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ── Composant ligne de course ─────────────────────────────

function RaceRow({
  race,
  token,
  predictedIbuId,
}: {
  race: RaceInfo;
  token: string;
  predictedIbuId: string;
}) {
  const [open, setOpen] = useState(false);
  const [results, setResults] = useState<RaceResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function toggle() {
    if (!open && results === null) {
      setLoading(true);
      setError("");
      try {
        const data = await calendar.results(race.race_id, token);
        setResults(data);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Erreur de chargement");
      } finally {
        setLoading(false);
      }
    }
    setOpen((v) => !v);
  }

  const disciplineColor = DISCIPLINE_COLORS[race.discipline] ?? "bg-gray-100 text-gray-600";
  const genderColor = GENDER_COLORS[race.gender] ?? "bg-gray-100 text-gray-500";

  return (
    <div className="border-b border-gray-50 last:border-0">
      <div className="flex items-center gap-3 py-2.5 px-1">
        {/* Date */}
        <span className="text-xs text-gray-400 w-24 shrink-0">
          {formatDate(race.start_time)}
        </span>

        {/* Badges discipline + genre */}
        <div className="flex items-center gap-1.5 shrink-0">
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${disciplineColor}`}>
            {race.discipline_display}
          </span>
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${genderColor}`}>
            {GENDER_LABEL[race.gender] ?? race.gender}
          </span>
        </div>

        {/* Bouton résultats */}
        <div className="ml-auto shrink-0">
          {race.is_past ? (
            <button
              onClick={toggle}
              className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-medium transition-colors"
            >
              {loading ? "Chargement…" : open ? "Masquer" : "Résultats"}
              {!loading && (
                <svg
                  className={`w-3.5 h-3.5 transition-transform ${open ? "rotate-180" : ""}`}
                  fill="none" stroke="currentColor" viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              )}
            </button>
          ) : (
            <span className="text-xs text-gray-300">À venir</span>
          )}
        </div>
      </div>

      {/* Résultats dépliés */}
      {open && (
        <div className="pb-3 px-1">
          {error ? (
            <p className="text-xs text-red-500">{error}</p>
          ) : (
            <ResultsTable results={results ?? []} predictedIbuId={predictedIbuId} />
          )}
        </div>
      )}
    </div>
  );
}

// ── Composant venue ───────────────────────────────────────

function VenueCard({
  venue,
  token,
  racePronos,
}: {
  venue: VenueInfo;
  token: string;
  racePronos: Record<string, string>;
}) {
  const ongoing = isOngoing(venue.start_date, venue.end_date);
  const allPast = venue.races.every((r) => r.is_past);
  const allFuture = venue.races.every((r) => !r.is_past);

  return (
    <div className={`bg-white rounded-2xl border shadow-sm overflow-hidden ${
      ongoing ? "border-blue-300 ring-1 ring-blue-200" : "border-gray-200"
    }`}>
      {/* En-tête venue */}
      <div className={`px-5 py-3 flex items-center justify-between ${
        ongoing ? "bg-blue-50" : allPast ? "bg-gray-50" : "bg-white"
      }`}>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-900">📍 {venue.location}</span>
            {ongoing && (
              <span className="text-xs font-medium bg-blue-600 text-white px-2 py-0.5 rounded-full animate-pulse">
                En cours
              </span>
            )}
          </div>
          <p className="text-xs text-gray-500 mt-0.5">
            {formatDateRange(venue.start_date, venue.end_date)}
          </p>
        </div>
        <div className="text-right text-xs text-gray-400">
          {allPast ? "✅ Terminé" : allFuture ? "🗓 Planifié" : ""}
        </div>
      </div>

      {/* Liste des courses */}
      <div className="px-4 py-1">
        {venue.races.map((race) => (
          <RaceRow key={race.race_id} race={race} token={token} predictedIbuId={racePronos[race.race_id] ?? ""} />
        ))}
      </div>
    </div>
  );
}

// ── Page principale ───────────────────────────────────────

export default function CalendrierPage() {
  const { user } = useAuth();
  const router = useRouter();

  const [venues, setVenues] = useState<VenueInfo[]>([]);
  const [racePronos, setRacePronos] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user) {
      router.push("/login");
      return;
    }

    const token = user.token;

    Promise.all([
      calendar.venues(token),
      racePronostics.get(token).catch(() => ({ pronos: {} })),
    ]).then(([venueData, pronosData]) => {
      setVenues(venueData);
      setRacePronos(pronosData.pronos);
    })
    .catch((e: unknown) => setError(e instanceof Error ? e.message : "Erreur de chargement"))
    .finally(() => setLoading(false));
  }, [user, router]);

  if (!user) return null;

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-1">
        <h1 className="text-2xl font-bold text-gray-900">📅 Calendrier & Résultats</h1>
        <Link
          href="/pronostics/modifier/course"
          className="text-sm text-blue-600 hover:text-blue-800 font-medium transition-colors"
        >
          🎯 Mes pronos →
        </Link>
      </div>
      <p className="text-sm text-gray-500 mb-6">
        Saison 2025/26 · Coupe du Monde IBU · Épreuves individuelles uniquement
        <span className="ml-2 text-yellow-600">· ★ = ton pronostic vainqueur</span>
      </p>

      {loading && (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-32 bg-gray-100 rounded-2xl animate-pulse" />
          ))}
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {!loading && !error && (
        <div className="space-y-4">
          {venues.map((venue) => (
            <VenueCard
              key={venue.event_id}
              venue={venue}
              token={user.token}
              racePronos={racePronos}
            />
          ))}
          {venues.length === 0 && (
            <p className="text-center text-gray-400 py-12">Aucune compétition trouvée.</p>
          )}
        </div>
      )}
    </div>
  );
}
