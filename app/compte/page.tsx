"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { auth, UserPublic } from "@/lib/api";

const FEEDBACK_TYPES = ["Suggestion", "Bug", "Amélioration", "Autre"];

export default function ComptePage() {
  const { user, signIn } = useAuth();
  const router = useRouter();

  const [profile, setProfile] = useState<UserPublic | null>(null);
  const [loading, setLoading] = useState(true);

  // Username
  const [newUsername, setNewUsername] = useState("");
  const [usernameMsg, setUsernameMsg] = useState("");

  // Password
  const [oldPwd, setOldPwd] = useState("");
  const [newPwd, setNewPwd] = useState("");
  const [confirmPwd, setConfirmPwd] = useState("");
  const [pwdMsg, setPwdMsg] = useState("");

  // Feedback
  const [fbType, setFbType] = useState("Suggestion");
  const [fbSubject, setFbSubject] = useState("");
  const [fbMessage, setFbMessage] = useState("");
  const [fbMsg, setFbMsg] = useState("");

  useEffect(() => {
    if (!user) { router.push("/login"); return; }
    auth.me(user.token).then((p) => {
      setProfile(p);
      setNewUsername(p.username);
    }).finally(() => setLoading(false));
  }, [user, router]);

  async function handleUsername(e: React.SyntheticEvent) {
    e.preventDefault();
    if (!user) return;
    setUsernameMsg("");
    try {
      const updated = await auth.updateUsername(newUsername, user.token);
      setProfile(updated);
      signIn({ ...user, username: updated.username });
      setUsernameMsg("✅ Pseudo mis à jour !");
    } catch (err: unknown) {
      setUsernameMsg(err instanceof Error ? err.message : "Erreur");
    }
  }

  async function handlePassword(e: React.SyntheticEvent) {
    e.preventDefault();
    if (!user) return;
    setPwdMsg("");
    if (newPwd !== confirmPwd) { setPwdMsg("Les mots de passe ne correspondent pas."); return; }
    if (newPwd.length < 6) { setPwdMsg("Au moins 6 caractères."); return; }
    try {
      const res = await auth.updatePassword(oldPwd, newPwd, user.token);
      setPwdMsg(`✅ ${res.detail}`);
      setOldPwd(""); setNewPwd(""); setConfirmPwd("");
    } catch (err: unknown) {
      setPwdMsg(err instanceof Error ? err.message : "Erreur");
    }
  }

  async function handleFeedback(e: React.SyntheticEvent) {
    e.preventDefault();
    if (!user) return;
    setFbMsg("");
    try {
      await auth.feedback(fbType, fbSubject, fbMessage, user.token);
      setFbMsg("✅ Merci pour ton feedback !");
      setFbSubject(""); setFbMessage("");
    } catch (err: unknown) {
      setFbMsg(err instanceof Error ? err.message : "Erreur");
    }
  }

  if (loading) return (
    <div className="flex justify-center items-center min-h-[60vh] text-gray-400">Chargement...</div>
  );

  return (
    <main className="max-w-2xl mx-auto px-4 py-8 space-y-8">
      <h1 className="text-2xl font-bold text-gray-900">👤 Mon Compte</h1>

      {/* Infos */}
      <section className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="font-semibold text-gray-800 mb-3">📄 Informations du compte</h2>
        <p className="text-sm text-gray-600"><span className="font-medium">Pseudo :</span> {profile?.username}</p>
        <p className="text-sm text-gray-600 mt-1"><span className="font-medium">Email :</span> {profile?.email}</p>
      </section>

      {/* Changer pseudo */}
      <section className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="font-semibold text-gray-800 mb-3">✏️ Changer mon pseudo</h2>
        <form onSubmit={handleUsername} className="space-y-3">
          <input
            type="text"
            value={newUsername}
            onChange={(e) => setNewUsername(e.target.value)}
            maxLength={30}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
            💾 Enregistrer
          </button>
          {usernameMsg && (
            <p className={`text-sm ${usernameMsg.startsWith("✅") ? "text-green-600" : "text-red-600"}`}>
              {usernameMsg}
            </p>
          )}
        </form>
      </section>

      {/* Changer mot de passe */}
      <section className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="font-semibold text-gray-800 mb-3">🔐 Changer mon mot de passe</h2>
        <form onSubmit={handlePassword} className="space-y-3">
          <input
            type="password"
            value={oldPwd}
            onChange={(e) => setOldPwd(e.target.value)}
            placeholder="Ancien mot de passe"
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="password"
            value={newPwd}
            onChange={(e) => setNewPwd(e.target.value)}
            placeholder="Nouveau mot de passe"
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="password"
            value={confirmPwd}
            onChange={(e) => setConfirmPwd(e.target.value)}
            placeholder="Confirmer le nouveau mot de passe"
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
            Mettre à jour
          </button>
          {pwdMsg && (
            <p className={`text-sm ${pwdMsg.startsWith("✅") ? "text-green-600" : "text-red-600"}`}>
              {pwdMsg}
            </p>
          )}
        </form>
      </section>

      {/* Feedback */}
      <section className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="font-semibold text-gray-800 mb-1">💬 Feedback & Suggestions</h2>
        <p className="text-sm text-gray-500 mb-3">Ton avis compte ! N&apos;hésite pas à partager tes idées ou signaler un bug.</p>
        <form onSubmit={handleFeedback} className="space-y-3">
          <select
            value={fbType}
            onChange={(e) => setFbType(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {FEEDBACK_TYPES.map((t) => <option key={t}>{t}</option>)}
          </select>
          <input
            type="text"
            value={fbSubject}
            onChange={(e) => setFbSubject(e.target.value)}
            placeholder="Sujet"
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <textarea
            value={fbMessage}
            onChange={(e) => setFbMessage(e.target.value)}
            placeholder="Message"
            required
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
          <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
            Envoyer
          </button>
          {fbMsg && <p className="text-sm text-green-600">{fbMsg}</p>}
        </form>
      </section>
    </main>
  );
}
