"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";

interface AuthUser {
  user_id: string;
  username: string;
  token: string;
}

interface CurrentLeague {
  league_id: string;
  name: string;
}

interface AuthContextType {
  user: AuthUser | null;
  currentLeague: CurrentLeague | null;
  hasPronos: boolean;
  signIn: (user: AuthUser) => void;
  signOut: () => void;
  selectLeague: (league: CurrentLeague | null) => void;
  setHasPronos: (value: boolean) => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [currentLeague, setCurrentLeague] = useState<CurrentLeague | null>(null);
  const [hasPronos, setHasPronosState] = useState<boolean>(false);

  useEffect(() => {
    const storedUser = localStorage.getItem("auth");
    if (storedUser) setUser(JSON.parse(storedUser));
    const storedLeague = localStorage.getItem("currentLeague");
    if (storedLeague) setCurrentLeague(JSON.parse(storedLeague));
    const storedPronos = localStorage.getItem("hasPronos");
    if (storedPronos === "true") setHasPronosState(true);
  }, []);

  const signIn = (user: AuthUser) => {
    setUser(user);
    localStorage.setItem("auth", JSON.stringify(user));
  };

  const signOut = () => {
    setUser(null);
    setCurrentLeague(null);
    setHasPronosState(false);
    localStorage.removeItem("auth");
    localStorage.removeItem("currentLeague");
    localStorage.removeItem("hasPronos");
  };

  const selectLeague = (league: CurrentLeague | null) => {
    setCurrentLeague(league);
    if (league) localStorage.setItem("currentLeague", JSON.stringify(league));
    else localStorage.removeItem("currentLeague");
  };

  const setHasPronos = (value: boolean) => {
    setHasPronosState(value);
    localStorage.setItem("hasPronos", String(value));
  };

  return (
    <AuthContext.Provider value={{ user, currentLeague, hasPronos, signIn, signOut, selectLeague, setHasPronos }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth doit être utilisé dans AuthProvider");
  return ctx;
}
