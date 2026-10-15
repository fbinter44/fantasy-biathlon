"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { auth } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import Logo from "@/components/Logo";

type Status = "loading" | "success" | "error";

function VerifyEmail() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { signIn, setHasPronos } = useAuth();
  const [status, setStatus] = useState<Status>("loading");
  const [error, setError] = useState("");
  // Le token est à usage unique : sans ce garde, le double appel des effets en
  // mode strict (dev) consommerait le token puis afficherait "déjà utilisé".
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    const token = searchParams?.get("token");
    if (!token) {
      setError("Lien d'activation incomplet.");
      setStatus("error");
      return;
    }
    auth.verifyEmail(token)
      .then((data) => {
        signIn({ user_id: data.user_id, username: data.username, token: data.access_token });
        setHasPronos(false); // compte tout neuf : aucun prono saisi
        setStatus("success");
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Erreur lors de l'activation");
        setStatus("error");
      });
  }, [searchParams, signIn, setHasPronos]);

  const btnClass = "w-full py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors";

  return (
    <div className="text-center space-y-4">
      {status === "loading" && (
        <p className="text-sm text-gray-500">Activation de ton compte en cours...</p>
      )}
      {status === "success" && (
        <>
          <div className="text-4xl">✅</div>
          <p className="font-medium text-gray-800">Ton compte est activé !</p>
          <p className="text-sm text-gray-500">Bienvenue sur Clean Shot, tu es maintenant connecté.</p>
          <button onClick={() => router.push("/")} className={btnClass}>
            C&apos;est parti
          </button>
        </>
      )}
      {status === "error" && (
        <>
          <div className="text-4xl">⚠️</div>
          <p className="text-sm text-red-700">{error}</p>
          <p className="text-sm text-gray-500">
            Si ton compte n&apos;est pas encore activé, connecte-toi pour recevoir un nouveau lien.
          </p>
          <button onClick={() => router.push("/login")} className={btnClass}>
            Aller à la connexion
          </button>
        </>
      )}
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="flex flex-col items-center mb-8">
          <Logo height={52} />
          <p className="text-gray-500 mt-2 text-sm">Activation du compte</p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
          {/* useSearchParams() exige une frontière Suspense au build (Next.js) */}
          <Suspense fallback={<p className="text-center text-sm text-gray-500">Chargement...</p>}>
            <VerifyEmail />
          </Suspense>
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
