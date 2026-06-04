"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { leagues, LeagueResponse } from "@/lib/api";

export default function LiguesPage() {
  const { user, currentLeague, selectLeague } = useAuth();
  const router = useRouter();

  const [myLeagues, setMyLeagues] = useState<LeagueResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [newName, setNewName] = useState("");
  const [joinCode, setJoinCode] = useState("");
  const [actionMsg, setActionMsg] = useState("");

  const fetchLeagues = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    try {
      const items = await leagues.mine(user.token);
      const details = await Promise.all(
        items.map((l) => leagues.get(l.league_id, user.token))
      );
      setMyLeagues(details);
      if (currentLeague && !details.some((l) => l.league_id === currentLeague.league_id)) {
        selectLeague(null);
      }
    } catch {
      setError("Impossible de charger les ski clubs.");
    } finally {
      setLoading(false);
    }
  }, [user, currentLeague, selectLeague]);

  useEffect(() => {
    if (!user) { router.push("/login"); return; }
    fetchLeagues();
  }, [user, router, fetchLeagues]);

  async function handleCreate(e: React.SyntheticEvent) {
    e.preventDefault();
    if (!user || !newName.trim()) return;
    try {
      await leagues.create(newName.trim(), user.token);
      setNewName("");
      setActionMsg(`Ski Club "${newName.trim()}" créé !`);
      fetchLeagues();
    } catch (err: unknown) {
      setActionMsg(err instanceof Error ? err.message : "Erreur");
    }
  }

  async function handleJoin(e: React.SyntheticEvent) {
    e.preventDefault();
    if (!user || !joinCode.trim()) return;
    try {
      const league = await leagues.join(joinCode.trim(), user.token);
      setJoinCode("");
      setActionMsg(`Tu as rejoint "${league.name}" !`);
      fetchLeagues();
    } catch (err: unknown) {
      setActionMsg(err instanceof Error ? err.message : "Erreur");
    }
  }

  async function handleDelete(league_id: string, name: string) {
    if (!user) return;
    try {
      await leagues.delete(league_id, user.token);
      if (currentLeague?.league_id === league_id) selectLeague(null);
      setActionMsg(`"${name}" a été supprimé.`);
      fetchLeagues();
    } catch (err: unknown) {
      setActionMsg(err instanceof Error ? err.message : "Erreur");
    }
  }

  async function handleLeave(league_id: string, name: string) {
    if (!user) return;
    try {
      await leagues.leave(league_id, user.token);
      if (currentLeague?.league_id === league_id) selectLeague(null);
      setActionMsg(`Tu as quitté "${name}".`);
      fetchLeagues();
    } catch (err: unknown) {
      setActionMsg(err instanceof Error ? err.message : "Erreur");
    }
  }

  if (loading) return (
    <div className="flex justify-center items-center min-h-[60vh] text-gray-400">
      Chargement...
    </div>
  );

  return (
    <main className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">🏔️ Mes Ski Clubs</h1>

      {/* Banner si pas de ligue sélectionnée */}
      {!currentLeague && (
        <div className="mb-6 p-4 bg-blue-50 border-l-4 border-blue-400 rounded text-blue-800 text-sm">
          <b>ℹ️ Sélectionne un ski club</b> pour accéder aux pronos, résultats et classements !
        </div>
      )}

      {/* Message retour action */}
      {actionMsg && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
          {actionMsg}
        </div>
      )}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Liste des ligues */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-gray-700 mb-3">🛠️ Gérer mes ski clubs</h2>
        {myLeagues.length === 0 ? (
          <p className="text-gray-500 text-sm">
            Tu ne fais partie d&apos;aucun ski club. Crée ou rejoins-en un ci-dessous !
          </p>
        ) : (
          <div className="space-y-3">
            {myLeagues.map((league) => {
              const isOwner = league.owner_id === user?.user_id;
              const isSelected = currentLeague?.league_id === league.league_id;
              return (
                <div
                  key={league.league_id}
                  className={`p-4 rounded-xl border ${isSelected ? "border-blue-400 bg-blue-50" : "border-gray-200 bg-white"}`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="font-semibold text-gray-900">
                      {league.name} {isOwner && "👑"}
                    </h3>
                    {isSelected && (
                      <span className="text-xs bg-blue-600 text-white px-2 py-0.5 rounded-full">
                        Sélectionné
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 mb-3">
                    <b>Membres :</b>{" "}
                    {league.members.map((m) => m.username).join(", ")}
                  </p>
                  {isOwner && (
                    <p className="text-sm text-gray-500 mb-3">
                      <b>Code d&apos;invitation :</b>{" "}
                      <span className="font-mono bg-gray-100 px-2 py-0.5 rounded">
                        {league.invite_code}
                      </span>
                    </p>
                  )}
                  <div className="flex gap-2 flex-wrap">
                    <button
                      onClick={() => selectLeague({ league_id: league.league_id, name: league.name })}
                      disabled={isSelected}
                      className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-40 transition-colors"
                    >
                      ➡️ Sélectionner
                    </button>
                    {isOwner ? (
                      <button
                        onClick={() => handleDelete(league.league_id, league.name)}
                        className="px-3 py-1.5 text-sm border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors"
                      >
                        🗑️ Supprimer
                      </button>
                    ) : (
                      <button
                        onClick={() => handleLeave(league.league_id, league.name)}
                        className="px-3 py-1.5 text-sm border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-50 transition-colors"
                      >
                        🚪 Quitter
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      <hr className="my-6 border-gray-200" />

      {/* Créer */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-gray-700 mb-3">➕ Créer un Ski Club</h2>
        <form onSubmit={handleCreate} className="flex gap-2">
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Nom du ski club"
            required
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            Créer
          </button>
        </form>
      </section>

      <hr className="my-6 border-gray-200" />

      {/* Rejoindre */}
      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-3">🔑 Rejoindre un Ski Club</h2>
        <form onSubmit={handleJoin} className="flex gap-2">
          <input
            type="text"
            value={joinCode}
            onChange={(e) => setJoinCode(e.target.value)}
            placeholder="Code d'invitation"
            required
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            Rejoindre
          </button>
        </form>
      </section>
    </main>
  );
}
