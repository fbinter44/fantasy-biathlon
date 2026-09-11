"use client";

import Link from "next/link";
import { useAuth } from "@/context/AuthContext";

export default function ConfidentialitePage() {
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

      <h1 className="text-2xl font-bold text-gray-900 mb-2">🔒 Politique de confidentialité</h1>
      <p className="text-gray-500 text-sm mb-8">
        Dernière mise à jour : septembre 2026
      </p>

      <section className="space-y-10 text-gray-700 text-sm leading-relaxed">

        {/* Intro */}
        <div className="bg-blue-50 border border-blue-100 rounded-xl px-5 py-4 text-blue-800 text-sm">
          Clean Shot est un jeu de fantasy biathlon à partager entre amis. Nous collectons uniquement
          les données strictement nécessaires au fonctionnement du jeu, sans publicité ni revente de données.
        </div>

        {/* 1. Responsable */}
        <div>
          <h2 className="text-base font-semibold text-gray-800 mb-3">1. Responsable du traitement</h2>
          <p>
            Le responsable du traitement des données est l'éditeur de l'application Clean Shot,
            accessible à l'adresse{" "}
            <a href="https://clean-shot.app" className="text-blue-600 hover:underline">clean-shot.app</a>.
          </p>
          <p className="mt-2">
            Pour toute question relative à la protection de vos données :{" "}
            <a href="mailto:support@clean-shot.app" className="text-blue-600 hover:underline">
              support@clean-shot.app
            </a>
          </p>
        </div>

        {/* 2. Données collectées */}
        <div>
          <h2 className="text-base font-semibold text-gray-800 mb-3">2. Données personnelles collectées</h2>
          <p className="mb-3">
            Nous collectons uniquement les données suivantes, toutes fournies volontairement lors
            de votre inscription ou utilisation de l'application :
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-gray-50">
                  <th className="text-left px-4 py-2.5 font-semibold text-gray-700 border-b border-gray-200">Donnée</th>
                  <th className="text-left px-4 py-2.5 font-semibold text-gray-700 border-b border-gray-200">Finalité</th>
                  <th className="text-left px-4 py-2.5 font-semibold text-gray-700 border-b border-gray-200">Base légale</th>
                </tr>
              </thead>
              <tbody>
                {[
                  ["Adresse email", "Connexion au compte, réinitialisation du mot de passe", "Exécution du contrat"],
                  ["Nom d'utilisateur (pseudo)", "Identification dans le jeu, classements", "Exécution du contrat"],
                  ["Mot de passe (hashé)", "Authentification sécurisée", "Exécution du contrat"],
                  ["Pronostics (prédictions saison & course)", "Calcul des scores, affichage du classement", "Exécution du contrat"],
                  ["Appartenance à un ski club (ligue)", "Fonctionnalités de groupe", "Exécution du contrat"],
                ].map(([donnee, finalite, base], i) => (
                  <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="px-4 py-2.5 font-medium text-gray-800">{donnee}</td>
                    <td className="px-4 py-2.5 text-gray-600">{finalite}</td>
                    <td className="px-4 py-2.5 text-gray-500">{base}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-gray-500">
            Aucune donnée sensible (santé, opinions, données financières) n'est collectée.
          </p>
        </div>

        {/* 3. Ce que nous ne faisons PAS */}
        <div>
          <h2 className="text-base font-semibold text-gray-800 mb-3">3. Ce que nous ne faisons pas</h2>
          <ul className="space-y-1.5">
            {[
              "Nous ne vendons pas vos données à des tiers.",
              "Nous n'utilisons pas de cookies publicitaires ou de traçage comportemental.",
              "Nous n'utilisons pas d'outils d'analytics tiers (Google Analytics, etc.).",
              "Nous ne partageons pas vos données avec des partenaires commerciaux.",
            ].map((item, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-green-500 mt-0.5 shrink-0">✓</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* 4. Stockage et sécurité */}
        <div>
          <h2 className="text-base font-semibold text-gray-800 mb-3">4. Stockage et sécurité</h2>
          <p>
            Vos données sont stockées dans une base de données PostgreSQL hébergée par{" "}
            <strong>Supabase</strong> (serveurs en Europe). Le backend de l'application est hébergé
            sur <strong>Railway</strong> et le frontend sur <strong>Vercel</strong>, des plateformes
            conformes au RGPD.
          </p>
          <p className="mt-2">Les mesures de sécurité incluent :</p>
          <ul className="mt-2 space-y-1.5">
            {[
              "Mots de passe hashés avec bcrypt (jamais stockés en clair).",
              "Communications chiffrées via HTTPS/TLS.",
              "Authentification par token JWT avec expiration automatique (7 jours).",
            ].map((item, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-blue-400 shrink-0 mt-0.5">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* 5. Durée de conservation */}
        <div>
          <h2 className="text-base font-semibold text-gray-800 mb-3">5. Durée de conservation</h2>
          <p>
            Vos données sont conservées tant que votre compte est actif. En cas d'inactivité prolongée
            (plus de 2 ans sans connexion), nous nous réservons le droit de supprimer votre compte
            après vous en avoir informé par email.
          </p>
          <p className="mt-2">
            Vous pouvez demander la suppression de votre compte à tout moment (voir article 7).
          </p>
        </div>

        {/* 6. Cookies */}
        <div>
          <h2 className="text-base font-semibold text-gray-800 mb-3">6. Cookies et stockage local</h2>
          <p>
            Clean Shot n'utilise <strong>pas de cookies</strong>. L'authentification repose sur un
            token JWT stocké dans le <em>localStorage</em> de votre navigateur, uniquement sur votre
            appareil. Ce token n'est pas transmis à des tiers et est effacé à la déconnexion.
          </p>
        </div>

        {/* 7. Vos droits */}
        <div>
          <h2 className="text-base font-semibold text-gray-800 mb-3">7. Vos droits (RGPD)</h2>
          <p className="mb-3">
            Conformément au Règlement Général sur la Protection des Données (RGPD — UE 2016/679),
            vous disposez des droits suivants :
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[
              { title: "Droit d'accès", desc: "Obtenir une copie de toutes vos données personnelles." },
              { title: "Droit de rectification", desc: "Corriger vos données inexactes ou incomplètes." },
              { title: "Droit à l'effacement", desc: "Demander la suppression de votre compte et de toutes vos données." },
              { title: "Droit à la portabilité", desc: "Recevoir vos données dans un format lisible (JSON)." },
              { title: "Droit d'opposition", desc: "Vous opposer à certains traitements de vos données." },
              { title: "Droit de limitation", desc: "Demander la suspension temporaire du traitement." },
            ].map(({ title, desc }) => (
              <div key={title} className="bg-gray-50 rounded-xl px-4 py-3 border border-gray-100">
                <p className="font-medium text-gray-800 text-sm">{title}</p>
                <p className="text-gray-500 text-xs mt-0.5">{desc}</p>
              </div>
            ))}
          </div>
          <p className="mt-4">
            Pour exercer ces droits, contactez-nous à{" "}
            <a href="mailto:support@clean-shot.app" className="text-blue-600 hover:underline">
              support@clean-shot.app
            </a>. Nous répondons sous <strong>30 jours</strong>.
          </p>
          <p className="mt-2">
            Si vous estimez que vos droits ne sont pas respectés, vous pouvez déposer une réclamation
            auprès de la <strong>CNIL</strong> :{" "}
            <a href="https://www.cnil.fr/fr/plaintes" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
              cnil.fr/fr/plaintes
            </a>.
          </p>
        </div>

        {/* 8. Tiers */}
        <div>
          <h2 className="text-base font-semibold text-gray-800 mb-3">8. Sous-traitants et tiers</h2>
          <p className="mb-3">
            Nous faisons appel aux prestataires suivants, chacun soumis à des garanties de conformité RGPD :
          </p>
          <div className="space-y-2">
            {[
              { name: "Supabase", role: "Hébergement de la base de données", pays: "UE", lien: "https://supabase.com/privacy" },
              { name: "Railway", role: "Hébergement du backend API", pays: "UE/US", lien: "https://railway.app/legal/privacy" },
              { name: "Vercel", role: "Hébergement du frontend", pays: "UE/US", lien: "https://vercel.com/legal/privacy-policy" },
              { name: "Brevo", role: "Envoi d'emails transactionnels", pays: "UE (🇫🇷)", lien: "https://www.brevo.com/legal/privacypolicy/" },
            ].map(({ name, role, pays, lien }) => (
              <div key={name} className="flex items-start gap-3 py-2 border-b border-gray-100 last:border-0">
                <div className="flex-1">
                  <span className="font-medium text-gray-800">{name}</span>
                  <span className="text-gray-400 mx-1.5">—</span>
                  <span className="text-gray-600">{role}</span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">{pays}</span>
                  <a href={lien} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-500 hover:underline">
                    Politique →
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 9. Modifications */}
        <div>
          <h2 className="text-base font-semibold text-gray-800 mb-3">9. Modifications</h2>
          <p>
            Cette politique peut être mise à jour. En cas de modification substantielle, nous vous en
            informerons par email. La date de dernière mise à jour figure en haut de cette page.
          </p>
        </div>

        {/* Contact */}
        <div className="bg-gray-50 rounded-xl px-5 py-4 border border-gray-200">
          <p className="font-medium text-gray-800 mb-1">Contact</p>
          <p className="text-gray-500">
            Pour toute question relative à cette politique ou à vos données :{" "}
            <a href="mailto:support@clean-shot.app" className="text-blue-600 hover:underline">
              support@clean-shot.app
            </a>
          </p>
        </div>

      </section>
    </main>
  );
}
