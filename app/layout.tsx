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
  title: "MPG Biathlon",
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
            <AppGuard>
              {children}
            </AppGuard>
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
