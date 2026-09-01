"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { athletes, pronostics, AthleteResponse, Top5, GlobeWinners } from "@/lib/api";
import AthleteSelect from "@/components/AthleteSelect";

const DEADLINE = new Date("2026-10-12T23:59:00");
const TOTAL_FIELDS = 18; // 5 + 5 + 4 + 4

const RANK_STYLES = [
  { bg: "bg-yellow-400", text: "text-yellow-900", label: "1er" },
  { bg: "bg-gray-300",   text: "text-gray-700",   label: "2e" },
  { bg: "bg-amber-600",  text: "text-amber-50",   label: "3e" },
  { bg: "bg-gray-100",   text: "text-gray-500",   label: "4e" },
  { bg: "bg-gray-100",   text: "text-gray-500",   label: "5e" },
];

const GLOBE_DISCIPLINES = [
  { key: "sprint",      label: "Sprint",     icon: "⚡" },
  { key: "pursuit",     label: "Poursuite",  icon: "🎿" },
  { key: "individual",  label: "Individuel", icon: "🎯" },
  { key: "mass_start",  label: "Mass Start", icon: "🏁" },
] as const;

function emptyTop5(): Top5 { return { p1:"", p2:"", p3:"", p4:"", p5:"" }; }
function emptyGlobes(): GlobeWinners {
  return { sprint_h:"", sprint_f:"", pursuit_h:"", pursuit_f:"",
           individual_h:"", individual_f:"", mass_start_h:"", mass_start_f:"" };
}

interface GenderCardProps {
  gender: "h" | "f";
  label: string;
  emoji: string;
  athleteList: AthleteResponse[];
  top5: Top5;
  onTop5Change: (pos: keyof Top5, val: string) => void;
  globes: GlobeWinners;
  onGlobeChange: (key: keyof GlobeWinners, val: string) => void;
  disabled: boolean;
  hasDuplicates: boolean;
}

function GenderCard({
  gender, label, emoji, athleteList,
  top5, onTop5Change, globes, onGlobeChange,
  disabled, hasDuplicates,
}: GenderCardProps) {
  const top5Keys = ["p1","p2","p3","p4","p5"] as (keyof Top5)[];
  const filledTop5 = Object.values(top5).filter(Boolean).length;
  const filledGlobes = GLOBE_DISCIPLINES.filter(
    ({ key }) => globes[`${key}_${gender}` as keyof GlobeWinners]
  ).length;

  return (
    <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm">
      {/* Header de la carte */}
      <div className={`px-5 py-4 ${gender === "h" ? "bg-blue-600" : "bg-pink-500"}`}>
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-white">{emoji} {label}</h2>
          <span className="text-sm text-white/80">
            {filledTop5 + filledGlobes}/9 remplis
          </span>
        </div>
      </div>

      <div className="p-5 space-y-6">
        {/* Top 5 */}
        <div>
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
            🏆 Top 5 Général
          </h3>
          {hasDuplicates && (
            <p className="text-xs text-red-500 mb-2">
              ⚠️ Doublon détecté dans le Top 5
            </p>
          )}
          <div className="space-y-2">
            {top5Keys.map((pos, i) => {
              const { bg, text, label: rankLabel } = RANK_STYLES[i];
              return (
                <div key={pos} className="flex items-center gap-3">
                  <span className={`w-8 h-8 rounded-full ${bg} ${text} text-xs font-bold flex items-center justify-center shrink-0`}>
                    {rankLabel}
                  </span>
                  <div className="flex-1">
                    <AthleteSelect
                      athletes={athleteList}
                      value={top5[pos]}
                      onChange={(v) => onTop5Change(pos, v)}
                      exclude={Object.values(top5).filter((v) => v && v !== top5[pos])}
                      disabled={disabled}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Globes */}
        <div>
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
            🌍 Globes de cristal
          </h3>
          <div className="space-y-2">
            {GLOBE_DISCIPLINES.map(({ key, label: discLabel, icon }) => {
              const globeKey = `${key}_${gender}` as keyof GlobeWinners;
              const isFilled = !!globes[globeKey];
              return (
                <div key={key} className={`flex items-center gap-3 p-2 rounded-lg transition-colors ${isFilled ? "bg-gray-50" : ""}`}>
                  <span className="w-8 text-center text-lg shrink-0">{icon}</span>
                  <span className="w-20 text-sm text-gray-600 shrink-0">{discLabel}</span>
                  <div className="flex-1">
                    <AthleteSelect
                      athletes={athleteList}
                      value={globes[globeKey]}
                      onChange={(v) => onGlobeChange(globeKey, v)}
                      disabled={disabled}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ModifierPage() {
  const { user, setHasPronos } = useAuth();
  const router = useRouter();

  const [athletesH, setAthletesH] = useState<AthleteResponse[]>([]);
  const [athletesF, setAthletesF] = useState<AthleteResponse[]>([]);
  const [top5h, setTop5h] = useState<Top5>(emptyTop5());
  const [top5f, setTop5f] = useState<Top5>(emptyTop5());
  const [globes, setGlobes] = useState<GlobeWinners>(emptyGlobes());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");

  const deadlinePassed = new Date() > DEADLINE;

  useEffect(() => {
    if (!user) { router.push("/login"); return; }
    async function load() {
      try {
        const [ah, af, me] = await Promise.all([
          athletes.list("M"),
          athletes.list("W"),
          pronostics.me(user!.token).catch(() => null),
        ]);
        setAthletesH(ah);
        setAthletesF(af);
        if (me) { setTop5h(me.top5_h); setTop5f(me.top5_f); setGlobes(me.globes); }
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [user, router]);

  function setTop5hField(pos: keyof Top5, val: string) { setTop5h((p) => ({ ...p, [pos]: val })); }
  function setTop5fField(pos: keyof Top5, val: string) { setTop5f((p) => ({ ...p, [pos]: val })); }
  function setGlobeField(key: keyof GlobeWinners, val: string) { setGlobes((p) => ({ ...p, [key]: val })); }

  const filledCount =
    Object.values(top5h).filter(Boolean).length +
    Object.values(top5f).filter(Boolean).length +
    Object.values(globes).filter(Boolean).length;
  const progressPct = Math.round((filledCount / TOTAL_FIELDS) * 100);

  const top5hValues = Object.values(top5h).filter(Boolean);
  const top5fValues = Object.values(top5f).filter(Boolean);
  const hasDuplicatesH = new Set(top5hValues).size !== top5hValues.length;
  const hasDuplicatesF = new Set(top5fValues).size !== top5fValues.length;
  const allFilled = filledCount === TOTAL_FIELDS;
  const canSave = allFilled && !deadlinePassed && !hasDuplicatesH && !hasDuplicatesF;

  async function handleSave() {
    if (!user || !canSave) return;
    setSaving(true);
    setMsg("");
    try {
      await pronostics.update({ top5_h: top5h, top5_f: top5f, globes }, user.token);
      setHasPronos(true);
      setMsg("success");
    } catch (err: unknown) {
      setMsg(err instanceof Error ? err.message : "Erreur lors de la sauvegarde.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return (
    <div className="flex justify-center items-center min-h-[60vh] text-gray-400">Chargement...</div>
  );

  return (
    <main className="max-w-7xl mx-auto px-4 py-8">
      {/* Titre + progression */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-3">📝 Mes pronostics</h1>
        <div className="flex items-center gap-3">
          <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${progressPct}%`,
                backgroundColor: allFilled ? "#22c55e" : "#3b82f6",
              }}
            />
          </div>
          <span className="text-sm font-medium text-gray-500 shrink-0">
            {filledCount}/{TOTAL_FIELDS}
          </span>
        </div>
      </div>

      {/* Bannières */}
      {deadlinePassed && (
        <div className="mb-5 p-4 bg-yellow-50 border border-yellow-300 rounded-xl text-yellow-800 text-sm flex items-center gap-2">
          ⏰ La deadline est passée — tes pronostics sont verrouillés.
        </div>
      )}
      {msg === "success" && (
        <div className="mb-5 p-4 bg-green-50 border border-green-200 rounded-xl text-green-700 text-sm flex items-center gap-2">
          ✅ Tes pronostics ont été enregistrés avec succès !
        </div>
      )}
      {msg && msg !== "success" && (
        <div className="mb-5 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
          {msg}
        </div>
      )}

      {/* Deux cartes */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <GenderCard
          gender="h" label="Hommes" emoji="🧔"
          athleteList={athletesH}
          top5={top5h} onTop5Change={setTop5hField}
          globes={globes} onGlobeChange={setGlobeField}
          disabled={deadlinePassed} hasDuplicates={hasDuplicatesH}
        />
        <GenderCard
          gender="f" label="Femmes" emoji="👩"
          athleteList={athletesF}
          top5={top5f} onTop5Change={setTop5fField}
          globes={globes} onGlobeChange={setGlobeField}
          disabled={deadlinePassed} hasDuplicates={hasDuplicatesF}
        />
      </div>

      {/* Bouton sauvegarde */}
      {!deadlinePassed && (
        <div className="mt-8 flex items-center gap-4">
          <button
            onClick={handleSave}
            disabled={!canSave || saving}
            className="px-8 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 disabled:opacity-40 transition-colors shadow-sm"
          >
            {saving ? "Sauvegarde..." : "💾 Enregistrer mes pronostics"}
          </button>
          {!allFilled && (
            <span className="text-sm text-gray-400">
              Encore {TOTAL_FIELDS - filledCount} champ{TOTAL_FIELDS - filledCount > 1 ? "s" : ""} à remplir
            </span>
          )}
        </div>
      )}
    </main>
  );
}
