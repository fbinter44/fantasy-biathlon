"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import {
  calendar, racePronostics, athletes,
  VenueInfo, AthleteResponse,
} from "@/lib/api";
import { useSeason } from "@/context/SeasonContext";
import AthleteSelect from "@/components/AthleteSelect";

// ── Helpers ──────────────────────────────────────────────

const DISCIPLINE_COLORS: Record<string, string> = {
  sprint:     "bg-blue-100 text-blue-700",
  pursuit:    "bg-green-100 text-green-700",
  individual: "bg-orange-100 text-orange-700",
  mass_start: "bg-purple-100 text-purple-700",
};

const GENDER_LABEL: Record<string, string> = { Men: "H", Women: "F" };
const GENDER_COLORS: Record<string, string> = {
  Men:   "bg-sky-50 text-sky-600",
  Women: "bg-pink-50 text-pink-600",
};

function formatDateRange(start: string, end: string): string {
  const s = new Date(start);
  const e = new Date(end);
  const opts: Intl.DateTimeFormatOptions = { day: "numeric", month: "long", year: "numeric" };
  if (start === end) return s.toLocaleDateString("fr-FR", opts);
  if (s.getMonth() === e.getMonth())
    return `${s.getDate()}–${e.toLocaleDateString("fr-FR", opts)}`;
  return `${s.toLocaleDateString("fr-FR", { day: "numeric", month: "long" })} – ${e.toLocaleDateString("fr-FR", opts)}`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("fr-FR", { weekday: "short", day: "numeric", month: "short" });
}

// ── Composant ligne de course ─────────────────────────────

function RaceRow({
  race,
  athleteList,
  currentIbuId,
  locked,
  token,
  season,
  onSaved,
}: {
  race: { race_id: string; discipline: string; discipline_display: string; gender: string; start_time: string; is_past: boolean };
  athleteList: AthleteResponse[];
  currentIbuId: string;
  locked: boolean;
  token: string;
  season: string;
  onSaved: (race_id: string, ibu_id: string) => void;
}) {
  const [selected, setSelected] = useState(currentIbuId);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  // Sync si le prono chargé change après le montage
  useEffect(() => { setSelected(currentIbuId); }, [currentIbuId]);

  const isDirty = selected !== currentIbuId;

  async function handleSave() {
    if (!selected) return;
    setError("");
    setSaved(false);
    setSaving(true);
    try {
      await racePronostics.set(race.race_id, selected, token, season);
      onSaved(race.race_id, selected);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Erreur");
    } finally {
      setSaving(false);
    }
  }

  const disciplineColor = DISCIPLINE_COLORS[race.discipline] ?? "bg-gray-100 text-gray-600";
  const genderColor = GENDER_COLORS[race.gender] ?? "bg-gray-100 text-gray-500";
  const genderKey = race.gender === "Men" ? "M" : "W";

  return (
    <div className={`border-b border-gray-50 last:border-0 py-3 px-1 ${locked ? "opacity-60" : ""}`}>
      {/* Ligne info + badges */}
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs text-gray-400 w-28 shrink-0">{formatDate(race.start_time)}</span>
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${disciplineColor}`}>
          {race.discipline_display}
        </span>
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${genderColor}`}>
          {GENDER_LABEL[race.gender] ?? race.gender}
        </span>
        {locked && <span className="ml-auto text-xs text-gray-400">🔒 Terminée</span>}
      </div>

      {/* Sélecteur + bouton */}
      <div className="flex items-center gap-2">
        {locked ? (
          <div className="flex-1 px-3 py-1.5 bg-gray-100 rounded-lg text-sm text-gray-400 cursor-not-allowed select-none">
            {selected
              ? athleteList.find((a) => a.ibu_id === selected)?.label ?? selected
              : "—"}
          </div>
        ) : (
          <>
            <div className="flex-1">
              <AthleteSelect
                athletes={athleteList.filter((a) => a.gender === genderKey)}
                value={selected}
                onChange={setSelected}
                placeholder="Choisir un vainqueur…"
              />
            </div>
            <button
              onClick={handleSave}
              disabled={saving || !selected || !isDirty}
              title="Enregistrer"
              className="shrink-0 w-7 h-7 flex items-center justify-center bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {saving ? "…" : "🔒"}
            </button>
          </>
        )}

        {/* Feedback */}
        {saved && !saving && <span className="text-xs text-green-600 shrink-0">✓</span>}
        {error && <span className="text-xs text-red-500 shrink-0">{error}</span>}
      </div>
    </div>
  );
}

// ── Composant venue repliable ─────────────────────────────

function VenueBlock({
  venue,
  pronos,
  allAthletes,
  token,
  season,
  isReadOnly,
  onSaved,
}: {
  venue: VenueInfo;
  pronos: Record<string, string>;
  allAthletes: AthleteResponse[];
  token: string;
  season: string;
  isReadOnly: boolean;
  onSaved: (race_id: string, ibu_id: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const filled = venue.races.filter((r) => pronos[r.race_id]).length;
  const total = venue.races.length;

  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm">
      {/* En-tête cliquable */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full px-5 py-3 bg-gray-50 rounded-2xl flex items-center justify-between gap-3 hover:bg-gray-100 transition-colors"
      >
        <div className="text-left">
          <p className="font-semibold text-gray-900">📍 {venue.location}</p>
          <p className="text-xs text-gray-500 mt-0.5">{formatDateRange(venue.start_date, venue.end_date)}</p>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <span className={`text-xs font-medium ${filled === total ? "text-green-600" : "text-gray-400"}`}>
            {filled}/{total}
          </span>
          <svg
            className={`w-4 h-4 text-gray-400 transition-transform ${open ? "rotate-180" : ""}`}
            fill="none" stroke="currentColor" viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {/* Courses — visibles seulement si ouvert */}
      {open && (
        <div className="px-4 py-1 border-t border-gray-100">
          {venue.races.map((race) => (
            <RaceRow
              key={race.race_id}
              race={race}
              athleteList={allAthletes}
              currentIbuId={pronos[race.race_id] ?? ""}
              locked={race.is_past || isReadOnly}
              token={token}
              season={season}
              onSaved={onSaved}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Page principale ───────────────────────────────────────

export default function CourseParCoursePage() {
  const { user } = useAuth();
  const { selected, isReadOnly } = useSeason();
  const router = useRouter();

  const [venues, setVenues] = useState<VenueInfo[]>([]);
  const [pronos, setPronos] = useState<Record<string, string>>({});
  const [allAthletes, setAllAthletes] = useState<AthleteResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user) { router.push("/login"); return; }
    const token = user.token;

    Promise.all([
      calendar.venues(token, selected.code),
      racePronostics.get(token, selected.code),
      athletes.list(),
    ])
      .then(([venueData, pronosData, athleteData]) => {
        setVenues(venueData);
        setPronos(pronosData.pronos);
        setAllAthletes(athleteData);
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Erreur de chargement"))
      .finally(() => setLoading(false));
  }, [user, router, selected.code]);

  if (!user) return null;

  const totalRaces = venues.flatMap((v) => v.races).length;
  const filled = venues.flatMap((v) => v.races).filter((r) => pronos[r.race_id]).length;

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* En-tête */}
      <div className="flex items-center gap-3 mb-1">
        <button onClick={() => router.back()} className="text-gray-400 hover:text-gray-600 transition-colors">
          ← Retour
        </button>
      </div>
      <h1 className="text-2xl font-bold text-gray-900 mb-1">🎯 Pronos Course par Course</h1>
      <div className="flex items-center justify-between mb-1">
        <p className="text-sm text-gray-500">
          Pronostique le vainqueur de chaque épreuve · <span className="text-blue-600 font-medium">10 pts</span> par bon pronostic
        </p>
        <Link
          href="/calendrier"
          className="text-sm text-blue-600 hover:text-blue-800 font-medium transition-colors shrink-0 ml-4"
        >
          📅 Voir les résultats →
        </Link>
      </div>
      {!loading && (
        <p className="text-xs text-gray-400 mb-6">
          {filled} / {totalRaces} courses renseignées
          {filled === totalRaces && totalRaces > 0 && " ✅"}
        </p>
      )}

      {loading && (
        <div className="space-y-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-28 bg-gray-100 rounded-2xl animate-pulse" />
          ))}
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-700">{error}</div>
      )}

      {!loading && !error && (
        <div className="space-y-3">
          {venues.map((venue) => (
            <VenueBlock
              key={venue.event_id}
              venue={venue}
              pronos={pronos}
              allAthletes={allAthletes}
              token={user.token}
              season={selected.code}
              isReadOnly={isReadOnly}
              onSaved={(race_id, ibu_id) => setPronos((p) => ({ ...p, [race_id]: ibu_id }))}
            />
          ))}

          {venues.length === 0 && (
            <p className="text-center text-gray-400 py-12">Aucune course trouvée.</p>
          )}
        </div>
      )}
    </div>
  );
}
