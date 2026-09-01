"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";

export default function ModifierHubPage() {
  const { user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!user) router.push("/login");
  }, [user, router]);

  if (!user) return null;

  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center px-4">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">📝 Mes Pronos</h1>
      <p className="text-sm text-gray-500 mb-10">Quel type de pronostic veux-tu gérer ?</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 w-full max-w-xl">

        {/* Saison */}
        <Link
          href="/pronostics/modifier/saison"
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
          href="/pronostics/modifier/course"
          className="group flex flex-col items-center gap-4 bg-white border-2 border-gray-200 hover:border-blue-400 hover:shadow-md rounded-2xl p-8 transition-all"
        >
          <span className="text-5xl">🎯</span>
          <div className="text-center">
            <p className="text-lg font-semibold text-gray-900 group-hover:text-blue-700 transition-colors">
              Course par course
            </p>
            <p className="text-sm text-gray-400 mt-1">
              Vainqueur de chaque épreuve · 10 pts
            </p>
          </div>
        </Link>

      </div>
    </div>
  );
}
