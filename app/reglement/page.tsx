"use client";

import Link from "next/link";
import { useAuth } from "@/context/AuthContext";

export default function ReglementPage() {
  const { user } = useAuth();

  return (
    <main className="max-w-3xl mx-auto px-4 py-8">
      {!user && (
        <div className="mb-6">
          <Link
            href="/login"
            className="inline-flex items-center gap-1.5 text-sm text-gray-400 hover:text-blue-600 transition-colors"
          >
            ← Retour à la connexion
          </Link>
        </div>
      )}
      <h1 className="text-2xl font-bold text-gray-900 mb-2">📘 Règles du jeu</h1>
      <p className="text-gray-500 text-sm mb-8">Clean Shot, le jeu de Fantasy Biathlon à partager avec tes amis !</p>

      <section className="space-y-8 text-gray-700">

        {/* Objectif */}
        <div>
          <h2 className="text-lg font-semibold text-gray-800 mb-3">🎯 Objectif</h2>
          <p>
            Chaque joueur prédit les performances des biathlètes tout au long de la saison.
            Plus tes pronostics se rapprochent des résultats réels, plus tu marques de points.
          </p>
          <p className="mt-2">Il y a <strong>deux types de pronostics</strong> :</p>
          <ul className="list-disc list-inside mt-2 space-y-1.5">
            <li>
              <strong>Pronos Saison</strong> — à remplir avant la première course :{" "}
              Top 5 Hommes, Top 5 Femmes, et vainqueur de globe pour chacune des 4 disciplines (× 2 genres = <strong>8 globes</strong>)
            </li>
            <li>
              <strong>Pronos Course par course</strong> — à remplir avant chaque course :{" "}
              prédis le vainqueur de chaque épreuve individuellement
            </li>
          </ul>
        </div>

        <hr className="border-gray-200" />

        {/* Deadline */}
        <div>
          <h2 className="text-lg font-semibold text-gray-800 mb-3">⏱️ Deadlines</h2>

          <div className="space-y-3">
            <div className="p-4 bg-blue-50 border border-blue-100 rounded-xl text-sm">
              <p className="font-semibold text-blue-800 mb-1">🏔️ Pronos Saison</p>
              <p className="text-blue-700">
                Doivent être soumis <strong>avant la première course de la saison</strong>.
                Une fois la deadline passée, aucune modification n&apos;est possible — tes choix t&apos;accompagnent jusqu&apos;en mars.
              </p>
            </div>
            <div className="p-4 bg-amber-50 border border-amber-100 rounded-xl text-sm">
              <p className="font-semibold text-amber-800 mb-1">🎯 Pronos Course par course</p>
              <p className="text-amber-700">
                Peuvent être modifiés jusqu&apos;au <strong>départ de la course concernée</strong>.
                Une fois la course lancée, ton pronostic est verrouillé.
              </p>
            </div>
          </div>
        </div>

        <hr className="border-gray-200" />

        {/* Calcul des points */}
        <div>
          <h2 className="text-lg font-semibold text-gray-800 mb-4">🧮 Calcul des points</h2>

          {/* Top 5 */}
          <div className="mb-6">
            <h3 className="font-semibold text-gray-700 mb-2">1. Top 5 Général (Hommes &amp; Femmes)</h3>
            <p className="text-sm mb-3">
              Pour chacun des 5 biathlètes que tu as sélectionnés, si cet athlète <strong>figure dans le top 10 du classement général final</strong>,
              tu reçois des points selon sa <em>vraie</em> place en fin de saison — peu importe la place où tu l&apos;avais prédit.
            </p>

            <div className="overflow-x-auto rounded-xl border border-gray-200 mb-3">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left font-medium text-gray-600">Rang réel en fin de saison</th>
                    <th className="px-4 py-2 text-left font-medium text-gray-600">Points gagnés</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {[
                    ["1er", "90"], ["2ème", "75"], ["3ème", "65"], ["4ème", "55"],
                    ["5ème", "50"], ["6ème", "45"], ["7ème", "41"], ["8ème", "37"],
                    ["9ème", "34"], ["10ème", "31"],
                    ["11ème et au-delà", "0"],
                  ].map(([rank, pts]) => (
                    <tr key={rank} className={pts === "0" ? "bg-gray-50 text-gray-400" : "hover:bg-gray-50"}>
                      <td className="px-4 py-2">{rank}</td>
                      <td className="px-4 py-2 font-medium text-blue-600">{pts} pts</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="p-4 bg-blue-50 border border-blue-100 rounded-xl text-sm">
              <p className="font-semibold text-blue-800 mb-1">⭐ Bonus rang exact : +50 points</p>
              <p className="text-blue-700">
                Si la place réelle de l&apos;athlète en fin de saison correspond <em>exactement</em> au rang où tu l&apos;avais prédit,
                tu reçois un bonus de <strong>+50 points</strong>.
              </p>
            </div>

            <div className="mt-3 p-4 bg-gray-50 border border-gray-200 rounded-xl text-sm">
              <p className="font-semibold text-gray-700 mb-2">Exemple concret</p>
              <p className="text-gray-600">
                Tu places <strong>Fillon Maillet à la 2ème place</strong> dans ton top 5 hommes.
              </p>
              <ul className="mt-2 space-y-1 text-gray-600">
                <li>→ Il finit <strong>1er</strong> en fin de saison : tu gagnes <strong>90 pts</strong> (pas de bonus)</li>
                <li>→ Il finit <strong>2ème</strong> : tu gagnes <strong>75 + 50 = 125 pts</strong> ✨ (rang exact !)</li>
                <li>→ Il finit <strong>5ème</strong> : tu gagnes <strong>50 pts</strong> (pas de bonus)</li>
                <li>→ Il finit <strong>12ème</strong> : tu gagnes <strong>0 pt</strong></li>
              </ul>
            </div>
          </div>

          {/* Globes */}
          <div className="mb-6">
            <h3 className="font-semibold text-gray-700 mb-2">2. Globes de Cristal</h3>
            <p className="text-sm mb-3">
              Tu dois prédire le vainqueur du globe pour chacune des <strong>8 combinaisons</strong> discipline × genre :
            </p>
            <div className="grid grid-cols-2 gap-2 mb-3 text-sm">
              {[
                ["⚡ Sprint H", "⚡ Sprint F"],
                ["🎿 Poursuite H", "🎿 Poursuite F"],
                ["🎯 Individuel H", "🎯 Individuel F"],
                ["🏁 Mass Start H", "🏁 Mass Start F"],
              ].map(([h, f]) => (
                <div key={h} className="contents">
                  <div className="px-3 py-2 bg-gray-50 rounded-lg text-gray-600">{h}</div>
                  <div className="px-3 py-2 bg-gray-50 rounded-lg text-gray-600">{f}</div>
                </div>
              ))}
            </div>
            <div className="flex gap-4 text-sm">
              <div className="flex-1 p-3 bg-green-50 border border-green-200 rounded-xl text-center">
                <div className="font-bold text-green-700 text-lg">+50 pts</div>
                <div className="text-green-600">Bon vainqueur</div>
              </div>
              <div className="flex-1 p-3 bg-gray-50 border border-gray-200 rounded-xl text-center">
                <div className="font-bold text-gray-400 text-lg">0 pt</div>
                <div className="text-gray-400">Mauvais vainqueur</div>
              </div>
            </div>
          </div>

          {/* Course par course */}
          <div className="mb-6">
            <h3 className="font-semibold text-gray-700 mb-2">3. Course par course 🆕</h3>
            <p className="text-sm mb-3">
              Avant chaque épreuve, tu peux parier sur le <strong>vainqueur de la course</strong>.
              Chaque bonne prédiction rapporte <strong>10 points</strong>, indépendamment du reste.
            </p>
            <div className="flex gap-4 text-sm mb-3">
              <div className="flex-1 p-3 bg-amber-50 border border-amber-200 rounded-xl text-center">
                <div className="font-bold text-amber-700 text-lg">+10 pts</div>
                <div className="text-amber-600">Vainqueur exact</div>
              </div>
              <div className="flex-1 p-3 bg-gray-50 border border-gray-200 rounded-xl text-center">
                <div className="font-bold text-gray-400 text-lg">0 pt</div>
                <div className="text-gray-400">Mauvaise prédiction</div>
              </div>
            </div>
            <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl text-sm">
              <ul className="space-y-1 text-gray-600">
                <li>✅ Tu peux pronostiquer le même athlète pour plusieurs courses</li>
                <li>✅ Tu peux modifier ton choix jusqu&apos;au départ de la course</li>
                <li>🔒 Une fois la course commencée, ton pronostic est verrouillé définitivement</li>
                <li>📊 Tes pronos course par course sont visibles dans <strong>📅 Calendrier &amp; Résultats</strong></li>
              </ul>
            </div>
          </div>

          {/* Score max */}
          <div>
            <h3 className="font-semibold text-gray-700 mb-2">4. Score maximum théorique</h3>
            <div className="overflow-x-auto rounded-xl border border-gray-200 text-sm">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left font-medium text-gray-600">Catégorie</th>
                    <th className="px-4 py-2 text-right font-medium text-gray-600">Max possible</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  <tr>
                    <td className="px-4 py-2">Top 5 Hommes (90+75+65+55+50 + 5×50 bonus)</td>
                    <td className="px-4 py-2 text-right font-medium text-blue-600">585 pts</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2">Top 5 Femmes (90+75+65+55+50 + 5×50 bonus)</td>
                    <td className="px-4 py-2 text-right font-medium text-blue-600">585 pts</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2">Globes (8 × 50 pts)</td>
                    <td className="px-4 py-2 text-right font-medium text-blue-600">400 pts</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2">Courses (42 courses × 10 pts)</td>
                    <td className="px-4 py-2 text-right font-medium text-blue-600">420 pts</td>
                  </tr>
                  <tr className="bg-blue-50 font-semibold">
                    <td className="px-4 py-2 text-blue-800">Total maximum</td>
                    <td className="px-4 py-2 text-right text-blue-800">1 990 pts</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p className="text-xs text-gray-400 mt-1">
              * Théorique : suppose que tes 5 athlètes finissent 1er–5ème dans l&apos;ordre exact que tu as prédit, et que tu prédis correctement les 42 vainqueurs de course.
            </p>
          </div>
        </div>

        <hr className="border-gray-200" />

        {/* Ski Clubs */}
        <div>
          <h2 className="text-lg font-semibold text-gray-800 mb-3">🏔️ Ski Clubs</h2>
          <p className="text-sm">
            Crée ou rejoins un <strong>Ski Club</strong> pour te mesurer à tes amis. Chaque ski club a son propre classement,
            sa propre page d&apos;évolution et son tableau de détail des scores.
            Tu peux appartenir à plusieurs ski clubs simultanément.
          </p>
        </div>

        <hr className="border-gray-200" />

        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-xl">
          <p className="text-sm text-yellow-800">
            📌 <strong>Rappel :</strong> les pronos saison sont définitifs dès la première course.
            Les pronos course par course peuvent être modifiés jusqu&apos;au départ de chaque épreuve.
            Prends le temps de bien réfléchir à tes choix avant chaque deadline !
          </p>
        </div>

      </section>
    </main>
  );
}
