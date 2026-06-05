"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { auth } from "@/lib/api";

type Step = "email" | "code" | "done";

export default function ResetPasswordPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("email");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleEmailSubmit(e: React.SyntheticEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await auth.resetRequest(email);
      setStep("code");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setLoading(false);
    }
  }

  async function handleCodeSubmit(e: React.SyntheticEvent) {
    e.preventDefault();
    setError("");
    if (newPassword !== confirm) { setError("Les mots de passe ne correspondent pas."); return; }
    if (newPassword.length < 6) { setError("Au moins 6 caractères."); return; }
    setLoading(true);
    try {
      await auth.resetPassword(email, code, newPassword);
      setStep("done");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setLoading(false);
    }
  }

  const inputClass = "w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500";
  const btnClass = "w-full py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors";

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">🎯 Clean Shot</h1>
          <p className="text-gray-500 mt-1">Réinitialisation du mot de passe</p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
          {/* Indicateur d'étapes */}
          <div className="flex border-b border-gray-100">
            {[
              { key: "email", label: "Email" },
              { key: "code",  label: "Code" },
              { key: "done",  label: "Terminé" },
            ].map(({ key, label }, i) => {
              const steps = ["email", "code", "done"];
              const current = steps.indexOf(step);
              const idx = steps.indexOf(key);
              return (
                <div key={key} className="flex-1 py-3 text-center">
                  <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${
                    idx < current ? "text-green-600" :
                    idx === current ? "text-blue-600" :
                    "text-gray-300"
                  }`}>
                    <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
                      idx < current ? "bg-green-100" :
                      idx === current ? "bg-blue-100" :
                      "bg-gray-100"
                    }`}>
                      {idx < current ? "✓" : i + 1}
                    </span>
                    {label}
                  </span>
                </div>
              );
            })}
          </div>

          <div className="p-6">
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}

            {/* Étape 1 — Email */}
            {step === "email" && (
              <form onSubmit={handleEmailSubmit} className="space-y-4">
                <p className="text-sm text-gray-500">
                  Saisis ton adresse email. Tu recevras un code pour réinitialiser ton mot de passe.
                </p>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className={inputClass}
                  />
                </div>
                <button type="submit" disabled={loading} className={btnClass}>
                  {loading ? "Envoi..." : "Envoyer le code"}
                </button>
              </form>
            )}

            {/* Étape 2 — Code + nouveau MDP */}
            {step === "code" && (
              <form onSubmit={handleCodeSubmit} className="space-y-4">
                <p className="text-sm text-gray-500">
                  Un code a été envoyé à <strong>{email}</strong>. Saisis-le ci-dessous avec ton nouveau mot de passe.
                </p>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Code reçu par email</label>
                  <input
                    type="text"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    required
                    placeholder="ex: a1b2c3"
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nouveau mot de passe</label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Confirmer le mot de passe</label>
                  <input
                    type="password"
                    value={confirm}
                    onChange={(e) => setConfirm(e.target.value)}
                    required
                    className={inputClass}
                  />
                </div>
                <button type="submit" disabled={loading} className={btnClass}>
                  {loading ? "Réinitialisation..." : "Réinitialiser mon mot de passe"}
                </button>
                <button
                  type="button"
                  onClick={() => { setStep("email"); setError(""); }}
                  className="w-full py-2 text-sm text-gray-400 hover:text-gray-600"
                >
                  ← Changer d&apos;email
                </button>
              </form>
            )}

            {/* Étape 3 — Succès */}
            {step === "done" && (
              <div className="text-center space-y-4">
                <div className="text-4xl">✅</div>
                <p className="font-medium text-gray-800">Mot de passe réinitialisé !</p>
                <p className="text-sm text-gray-500">Tu peux maintenant te connecter avec ton nouveau mot de passe.</p>
                <button onClick={() => router.push("/login")} className={btnClass}>
                  Se connecter
                </button>
              </div>
            )}
          </div>
        </div>

        <p className="text-center mt-4 text-sm text-gray-400">
          <Link href="/login" className="hover:text-blue-600 underline underline-offset-2">
            ← Retour à la connexion
          </Link>
        </p>
      </div>
    </div>
  );
}
