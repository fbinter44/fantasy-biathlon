"use client";

import Link from "next/link";
import { useAuth } from "@/context/AuthContext";

interface FaqItem {
  q: string;
  a: React.ReactNode;
}

const FAQ_ITEMS: FaqItem[] = [
  {
    q: "Qui voit mes pronostics, et quand ?",
    a: (
      <>
        Personne ne voit les pronostics de personne avant la deadline de la saison, même pas les membres
        de ton propre ski club. Tes propres pronostics, eux, te sont toujours visibles. Une fois la deadline
        passée, tes coéquipiers de ski club peuvent voir tes pronos saison (et toi les leurs), mais pas les
        joueurs des autres clubs.
      </>
    ),
  },
  {
    q: "Quelle est la différence entre le classement général et le classement de mon ski club ?",
    a: (
      <>
        Le <strong>classement général</strong> (page 📊 Mes Résultats) te situe parmi{" "}
        <strong>tous les joueurs de l&apos;app</strong>, tous ski clubs confondus. Le{" "}
        <strong>classement du ski club</strong> ne compare que les membres d&apos;un club donné. Les points
        sont calculés de la même façon des deux côtés : seul le groupe de comparaison change.
      </>
    ),
  },
  {
    q: "Comment fonctionne un ski club ?",
    a: (
      <>
        Un ski club est juste un groupe d&apos;amis avec son propre classement. Tu peux en créer un (tu
        reçois un code d&apos;invitation à partager) ou en rejoindre un avec un code reçu, et tu peux
        appartenir à <strong>plusieurs ski clubs en même temps</strong>. Ce sont tes pronostics, un seul et
        même jeu de pronos, qui sont comparés dans chacun d&apos;eux (voir question suivante).
      </>
    ),
  },
  {
    q: "Est-ce que je peux avoir des pronostics différents selon le ski club ?",
    a: (
      <>
        Non : tes pronostics sont <strong>uniques, communs à tous tes ski clubs</strong>. Si tu es dans
        plusieurs clubs, c&apos;est le même Top 5, les mêmes globes et les mêmes pronos course par course qui
        comptent partout. Seul le classement affiché change d&apos;un club à l&apos;autre.
      </>
    ),
  },
  {
    q: "Je rejoins un ski club en cours de saison, ou j'ai raté la deadline des pronos saison, je fais quoi ?",
    a: (
      <>
        Tu peux rejoindre un ski club à tout moment. En revanche, la deadline des pronos saison est la même
        pour tout le monde : si elle est passée, tu ne peux plus soumettre de Top 5 ni de globes, et ces
        catégories resteront à 0 point pour toi cette saison. Tu peux en revanche toujours faire des{" "}
        <strong>pronos course par course</strong> pour toutes les courses à venir.
      </>
    ),
  },
  {
    q: "Un des biathlètes que j'ai choisi se blesse ou arrête la saison, qu'est-ce qui se passe ?",
    a: (
      <>
        Rien de spécial : pas d&apos;échange, pas de remboursement de points. S&apos;il sort du top 10 du
        classement général (ou n&apos;y entre jamais), il ne rapporte simplement plus de points, comme
        n&apos;importe quel athlète moins performant que prévu.
      </>
    ),
  },
  {
    q: "Je peux choisir n'importe quel biathlète, même à la retraite ?",
    a: (
      <>
        Oui ! Tous les biathlètes ayant déjà couru en IBU Cup sont sélectionnables, actifs ou non. Si tu
        veux chambrer et prendre Martin Fourcade en pariant sur un retour surprise… libre à toi 😏 (dans les
        listes de sélection, les athlètes actifs cette saison ou la précédente remontent en tête pour
        faciliter la recherche).
      </>
    ),
  },
  {
    q: "Un bug, une question, une suggestion ?",
    a: (
      <>
        N&apos;hésite pas à nous en faire part directement depuis{" "}
        <Link href="/compte" className="text-blue-600 hover:text-blue-800 underline underline-offset-2">
          Mon Compte
        </Link>{" "}
        (section 💬 Feedback &amp; Suggestions), on lit tout !
      </>
    ),
  },
];

export default function FaqPage() {
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

      <h1 className="text-2xl font-bold text-gray-900 mb-2">❓ FAQ</h1>
      <p className="text-gray-500 text-sm mb-8">
        Les questions qui reviennent souvent. Pour le détail du calcul des points, direction{" "}
        <Link href="/reglement" className="text-blue-600 hover:text-blue-800 underline underline-offset-2">
          📘 les règles du jeu
        </Link>
        .
      </p>

      <section className="space-y-4">
        {FAQ_ITEMS.map(({ q, a }) => (
          <div key={q} className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5">
            <h2 className="font-semibold text-gray-800 mb-2">{q}</h2>
            <p className="text-sm text-gray-600 leading-relaxed">{a}</p>
          </div>
        ))}
      </section>
    </main>
  );
}
