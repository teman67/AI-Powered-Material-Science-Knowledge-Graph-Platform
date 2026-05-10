"use client";

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

const TOKEN_KEY = "materials_kg_token";

type AuthContextValue = {
  token: string | null;
  setToken: (token: string | null) => void;
  ready: boolean;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const existing = window.localStorage.getItem(TOKEN_KEY);
    if (existing) {
      setTokenState(existing);
    }
    setReady(true);
  }, []);

  const setToken = (nextToken: string | null) => {
    setTokenState(nextToken);
    if (nextToken) {
      window.localStorage.setItem(TOKEN_KEY, nextToken);
    } else {
      window.localStorage.removeItem(TOKEN_KEY);
    }
  };

  const value = useMemo(
    () => ({
      token,
      setToken,
      ready,
    }),
    [token, ready]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }
  return context;
}
