"use client";

import { useState, useRef } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useSeason } from "@/context/SeasonContext";
import Logo from "@/components/Logo";

const NAV_PERSONAL = [
  { href: "/ligues",              label: "🏔️ Mes Ski Clubs" },
  { href: "/pronostics/modifier", label: "📝 Mes Pronos" },
  { href: "/compte",              label: "👤 Mon Compte" },
];

const NAV_LEAGUE = [
  { href: "/pronostics",           label: "🏔️ Pronos du Ski Club" },
  { href: "/pronostics/biathlete", label: "🔎 Focus Biathlète" },
  { href: "/classement",           label: "🏆 Classement du Ski Club" },
  { href: "/classement/detail",    label: "🔍 Détail des scores" },
];

const NAV_IBU = [
  { href: "/calendrier", label: "📅 Calendrier & Résultats" },
  { href: "/resultats",  label: "🏅 Classements généraux" },
];

// Pages accessibles en hors-saison (doit correspondre à BYPASS_PATHS dans AppGuard)
const OFFSEASON_ACCESSIBLE = new Set(["/ligues", "/compte", "/calendrier"]);

function DropdownMenu({
  items,
  onClose,
  isFutureSeason = false,
}: {
  items: { href: string; label: string }[];
  onClose: () => void;
  isFutureSeason?: boolean;
}) {
  const pathname = usePathname();
  return (
    <div className="absolute top-full left-0 mt-1 w-52 bg-white border border-gray-200 rounded-xl shadow-lg py-1 z-50">
      {items.map(({ href, label }) => {
        const blocked = isFutureSeason && !OFFSEASON_ACCESSIBLE.has(href);
        if (blocked) {
          return (
            <span
              key={href}
              title="Disponible à partir du 1er novembre"
              className="block px-4 py-2 text-sm text-gray-300 cursor-not-allowed select-none"
            >
              {label}
            </span>
          );
        }
        return (
          <Link
            key={href}
            href={href}
            onClick={onClose}
            className={`block px-4 py-2 text-sm transition-colors ${
              pathname === href
                ? "bg-blue-50 text-blue-700 font-medium"
                : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
            }`}
          >
            {label}
          </Link>
        );
      })}
    </div>
  );
}

export default function Header() {
  const { user, currentLeague, hasPronos, signOut } = useAuth();
  const { selected, setSelected, availableSeasons, isReadOnly, isFutureSeason } = useSeason();
  const router = useRouter();
  const pathname = usePathname();

  const [openMenu, setOpenMenu] = useState<"personal" | "league" | "ibu" | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [mobileSection, setMobileSection] = useState<"personal" | "league" | "ibu" | null>(null);
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  function enterMenu(menu: "personal" | "league" | "ibu") {
    if (closeTimer.current) clearTimeout(closeTimer.current);
    setOpenMenu(menu);
  }

  function leaveMenu() {
    closeTimer.current = setTimeout(() => setOpenMenu(null), 150);
  }

  function handleLogout() {
    signOut();
    setDrawerOpen(false);
    router.push("/login");
  }

  if (!user) return null;

  // Bandeau visible quand on consulte une saison archivée (≠ saison par défaut)
  const isViewingPastSeason = selected.code !== availableSeasons[0]?.code;

  return (
    <>
      {isFutureSeason && (
        <div className="bg-blue-50 border-b border-blue-200 px-4 py-1.5 text-center text-xs text-blue-700 sticky top-0 z-40">
          ⏳ La saison {selected.label} n&apos;a pas encore commencé — l&apos;espace pronos ouvrira le 1er novembre
        </div>
      )}
      {!isFutureSeason && isViewingPastSeason && (
        <div className="bg-amber-50 border-b border-amber-200 px-4 py-1.5 text-center text-xs text-amber-700 sticky top-0 z-40">
          📖 Consultation de la saison {selected.label} — lecture seule
        </div>
      )}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between gap-4">

          {/* Logo + sélecteur de saison */}
          <div className="flex items-center gap-3 shrink-0">
            <Link href="/ligues" aria-label="Clean Shot — accueil">
              <Logo height={36} />
            </Link>
            {availableSeasons.length > 1 && (
              <select
                value={selected.code}
                onChange={(e) => {
                  const s = availableSeasons.find((x) => x.code === e.target.value);
                  if (s) setSelected(s);
                }}
                className={`text-xs px-2 py-1 rounded-lg border transition-colors focus:outline-none ${
                  isReadOnly
                    ? "border-amber-300 bg-amber-50 text-amber-700"
                    : "border-gray-200 bg-gray-50 text-gray-600"
                }`}
              >
                {availableSeasons.map((s) => (
                  <option key={s.code} value={s.code}>{s.label}</option>
                ))}
              </select>
            )}
          </div>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-2">

            {/* Dropdown "Mon Coin Perso" */}
            <div
              className="relative"
              onMouseEnter={() => enterMenu("personal")}
              onMouseLeave={leaveMenu}
            >
              <button className={`flex items-center gap-1 px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                openMenu === "personal"
                  ? "bg-gray-100 text-gray-900"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              }`}>
                Mon Coin Perso
                <svg className="w-3.5 h-3.5 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {openMenu === "personal" && (
                <DropdownMenu items={NAV_PERSONAL} onClose={() => setOpenMenu(null)} isFutureSeason={isFutureSeason} />
              )}
            </div>

            {/* Dropdown "Le Coin de l'IBU" */}
            <div
              className="relative"
              onMouseEnter={() => enterMenu("ibu")}
              onMouseLeave={leaveMenu}
            >
              <button className={`flex items-center gap-1 px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                openMenu === "ibu"
                  ? "bg-gray-100 text-gray-900"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              }`}>
                Le Coin de l&apos;IBU
                <svg className="w-3.5 h-3.5 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {openMenu === "ibu" && (
                <DropdownMenu items={NAV_IBU} onClose={() => setOpenMenu(null)} isFutureSeason={isFutureSeason} />
              )}
            </div>

            {/* Dropdown "Mon Ski Club" — visible seulement si ligue sélectionnée */}
            {currentLeague && (
              <div
                className="relative"
                onMouseEnter={() => enterMenu("league")}
                onMouseLeave={leaveMenu}
              >
                <button className={`flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  hasPronos
                    ? openMenu === "league" ? "bg-blue-700 text-white" : "bg-blue-600 text-white hover:bg-blue-700"
                    : "bg-gray-200 text-gray-400 cursor-not-allowed"
                }`}>
                  🏔️ {currentLeague.name}
                  <svg className="w-3.5 h-3.5 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {openMenu === "league" && (
                  hasPronos
                    ? <DropdownMenu items={NAV_LEAGUE} onClose={() => setOpenMenu(null)} isFutureSeason={isFutureSeason} />
                    : (
                      <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-gray-200 rounded-xl shadow-lg p-4 z-50">
                        <p className="text-sm text-gray-500 text-center">
                          📝 Remplis tes pronos pour accéder à cette vue
                        </p>
                      </div>
                    )
                )}
              </div>
            )}
          </nav>

          {/* Desktop : règles + user + logout */}
          <div className="hidden md:flex items-center gap-3 shrink-0">
            <Link href="/reglement" className="text-sm text-gray-500 hover:text-gray-800 transition-colors">
              📘 Règles
            </Link>
            <span className="text-gray-200">|</span>
            <span className="text-sm text-gray-500">{user.username}</span>
            <button onClick={handleLogout} className="text-sm text-red-500 hover:text-red-700">
              Déconnexion
            </button>
          </div>

          {/* Mobile : hamburger */}
          <button
            className="md:hidden p-2 rounded-md text-gray-500 hover:bg-gray-100"
            onClick={() => setDrawerOpen(true)}
            aria-label="Menu"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>
      </header>

      {/* Mobile drawer */}
      {drawerOpen && (
        <>
          <div className="fixed inset-0 bg-black/30 z-40 md:hidden" onClick={() => setDrawerOpen(false)} />
          <div className="fixed top-0 right-0 h-full w-72 bg-white shadow-xl z-50 flex flex-col md:hidden">

            {/* Header */}
            <div className="flex items-center justify-between px-4 h-14 border-b border-gray-100">
              <Logo height={32} />
              <button onClick={() => setDrawerOpen(false)} className="p-2 text-gray-400 hover:text-gray-600">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto py-2">

              {/* Section Mon Coin Perso */}
              <div className="px-3">
                <button
                  onClick={() => setMobileSection(mobileSection === "personal" ? null : "personal")}
                  className="w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-semibold text-gray-700 hover:bg-gray-50"
                >
                  Mon Coin Perso
                  <svg className={`w-4 h-4 transition-transform ${mobileSection === "personal" ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {mobileSection === "personal" && (
                  <div className="mt-1 flex flex-col gap-0.5 pl-2">
                    {NAV_PERSONAL.map(({ href, label }) => {
                      const blocked = isFutureSeason && !OFFSEASON_ACCESSIBLE.has(href);
                      return blocked ? (
                        <span key={href} className="block px-3 py-2 text-sm text-gray-300 cursor-not-allowed select-none rounded-lg">
                          {label}
                        </span>
                      ) : (
                        <Link key={href} href={href} onClick={() => setDrawerOpen(false)} className="px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded-lg">
                          {label}
                        </Link>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Section Le Coin de l'IBU */}
              <div className="px-3 mt-1">
                <button
                  onClick={() => setMobileSection(mobileSection === "ibu" ? null : "ibu")}
                  className="w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-semibold text-gray-700 hover:bg-gray-50"
                >
                  Le Coin de l&apos;IBU
                  <svg className={`w-4 h-4 transition-transform ${mobileSection === "ibu" ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {mobileSection === "ibu" && (
                  <div className="mt-1 flex flex-col gap-0.5 pl-2">
                    {NAV_IBU.map(({ href, label }) => {
                      const blocked = isFutureSeason && !OFFSEASON_ACCESSIBLE.has(href);
                      return blocked ? (
                        <span key={href} className="block px-3 py-2 text-sm text-gray-300 cursor-not-allowed select-none rounded-lg">
                          {label}
                        </span>
                      ) : (
                        <Link key={href} href={href} onClick={() => setDrawerOpen(false)} className="px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded-lg">
                          {label}
                        </Link>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Section Mon Ski Club */}
              <div className="px-3 mt-1">
                {currentLeague ? (
                  <>
                    <button
                      onClick={() => setMobileSection(mobileSection === "league" ? null : "league")}
                      className="w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700"
                    >
                      🏔️ {currentLeague.name}
                      <svg className={`w-4 h-4 transition-transform ${mobileSection === "league" ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                    {mobileSection === "league" && (
                      <div className="mt-1 pl-2">
                        {hasPronos ? (
                          <div className="flex flex-col gap-0.5">
                            {NAV_LEAGUE.map(({ href, label }) => (
                              <Link
                                key={href}
                                href={href}
                                onClick={() => setDrawerOpen(false)}
                                className="px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded-lg"
                              >
                                {label}
                              </Link>
                            ))}
                          </div>
                        ) : (
                          <p className="px-3 py-2 text-sm text-gray-400 italic">
                            📝 Remplis tes pronos pour accéder à ces vues
                          </p>
                        )}
                      </div>
                    )}
                  </>
                ) : (
                  <Link
                    href="/ligues"
                    onClick={() => setDrawerOpen(false)}
                    className="block px-3 py-2.5 rounded-lg text-sm text-gray-400 border border-dashed border-gray-300 hover:border-blue-400 hover:text-blue-500 text-center"
                  >
                    Sélectionner un ski club…
                  </Link>
                )}
              </div>
            </div>

            {/* Footer */}
            <div className="px-5 py-4 border-t border-gray-100 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-600">{user.username}</span>
                <Link href="/reglement" onClick={() => setDrawerOpen(false)} className="text-sm text-gray-400 hover:text-gray-600">
                  📘 Règles
                </Link>
              </div>
              <button onClick={handleLogout} className="text-sm text-red-500 hover:text-red-700">
                Déconnexion
              </button>
            </div>
          </div>
        </>
      )}
    </>
  );
}
