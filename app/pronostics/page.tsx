"use client";

import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";

function PronosticsHubContent() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const pronosRequis = searchParams?.get("pronos_requis") === "1";

  useEffect(() => {
    if (authLoading) return;
    if (!user) router.push("/login");
  }, [user, authLoading, router]);

  if (authLoading || !user) return null;

  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center px-4">
      {pronosRequis && (
        <div className="w-full max-w-xl mb-8 p-4 bg-amber-50 border-2 border-amber-300 rounded-2xl text-center">
          <p className="text-amber-800 font-semibold">
            ⚠️ Remplis d&apos;abord tes pronos saison
          </p>
          <p className="text-sm text-amber-700 mt-1">
            Les pages de ton ski club (pronos, classement, détail des scores…) ne
            sont accessibles qu&apos;une fois tes pronos saison soumis.
          </p>
        </div>
      )}

      <h1 className="text-2xl font-bold text-gray-900 mb-2">📝 Mes Pronos</h1>
      <p className="text-sm text-gray-500 mb-10">Quel type de pronostics veux-tu gérer ?</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 w-full max-w-xl">

        {/* Saison */}
        <Link
          href="/pronostics/saison"
          className="group flex flex-col items-center gap-4 bg-white border-2 border-gray-200 hover:border-blue-400 hover:shadow-md rounded-2xl p-8 transition-all"
        >
          <span className="text-5xl">🏔️</span>
          <div className="text-center">
            <p className="text-lg font-semibold text-gray-900 group-hover:text-blue-700 transition-colors">
              Saison
            </p>
            <p className="text-sm text-gray-400 mt-1">
              Top 5 général et vainqueurs de globe
            </p>
          </div>
        </Link>

        {/* Course par course */}
        <Link
          href="/pronostics/course"
          className="group flex flex-col items-center gap-4 bg-white border-2 border-gray-200 hover:border-blue-400 hover:shadow-md rounded-2xl p-8 transition-all"
        >
          <span className="text-5xl">🎯</span>
          <div className="text-center">
            <p className="text-lg font-semibold text-gray-900 group-hover:text-blue-700 transition-colors">
              Course par course
            </p>
            <p className="text-sm text-gray-400 mt-1">
              Vainqueurs de chaque épreuve
            </p>
          </div>
        </Link>

      </div>
    </div>
  );
}

export default function PronosticsHubPage() {
  return (
    <Suspense fallback={null}>
      <PronosticsHubContent />
    </Suspense>
  );
}
