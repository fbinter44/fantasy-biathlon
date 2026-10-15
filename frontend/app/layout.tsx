import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import { SeasonProvider } from "@/context/SeasonContext";
import Header from "@/components/Header";
import AppGuard from "@/components/AppGuard";
import Link from "next/link";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Clean Shot",
  description: "Fantasy Biathlon 2025/26",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr" className={`${inter.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-gray-50">
        <AuthProvider>
          <SeasonProvider>
            <Header />
            {/* w-full nécessaire : body est flex-col, et sans largeur explicite
                un enfant flex direct (ici la page courante) peut se calculer
                plus large que le viewport dès qu'il contient un descendant
                large (ex. un tableau) — même avec overflow-x-auto dessus,
                qui ne suffit pas seul à contenir le débordement dans ce cas. */}
            <div className="w-full">
              <AppGuard>
                {children}
              </AppGuard>
            </div>
            <footer className="mt-auto border-t border-gray-100 bg-white">
              <div className="max-w-7xl mx-auto px-4 h-10 flex items-center justify-center gap-4 text-xs text-gray-400">
                <span>© 2026 Clean Shot</span>
                <span className="text-gray-300">·</span>
                <Link href="/confidentialite" className="hover:text-gray-600 transition-colors">
                  Politique de confidentialité
                </Link>
              </div>
            </footer>
          </SeasonProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
