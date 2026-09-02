import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import { SeasonProvider } from "@/context/SeasonContext";
import Header from "@/components/Header";
import AppGuard from "@/components/AppGuard";

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
          </SeasonProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
