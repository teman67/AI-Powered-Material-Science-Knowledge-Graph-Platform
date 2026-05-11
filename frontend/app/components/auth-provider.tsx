"use client";

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { getCurrentUser } from "../../lib/api";

const TOKEN_KEY = "materials_kg_token";
const USER_EMAIL_KEY = "materials_kg_user_email";

type AuthContextValue = {
  token: string | null;
  setToken: (token: string | null) => void;
  userEmail: string | null;
  setUserEmail: (email: string | null) => void;
  ready: boolean;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(null);
  const [userEmail, setUserEmailState] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const existing = window.localStorage.getItem(TOKEN_KEY);
    const existingEmail = window.localStorage.getItem(USER_EMAIL_KEY);
    if (existing) {
      setTokenState(existing);
    }
    if (existingEmail) {
      setUserEmailState(existingEmail);
    }
    setReady(true);
  }, []);

  useEffect(() => {
    if (!ready || !token || userEmail) {
      return;
    }

    let cancelled = false;
    getCurrentUser(token)
      .then((user) => {
        if (cancelled) {
          return;
        }
        const normalized = user.email.trim().toLowerCase();
        setUserEmailState(normalized);
        window.localStorage.setItem(USER_EMAIL_KEY, normalized);
      })
      .catch(() => {
        if (cancelled) {
          return;
        }
        setUserEmailState(null);
      });

    return () => {
      cancelled = true;
    };
  }, [ready, token, userEmail]);

  const setUserEmail = (nextEmail: string | null) => {
    const normalized = nextEmail ? nextEmail.trim().toLowerCase() : null;
    setUserEmailState(normalized);
    if (normalized) {
      window.localStorage.setItem(USER_EMAIL_KEY, normalized);
    } else {
      window.localStorage.removeItem(USER_EMAIL_KEY);
    }
  };

  const setToken = (nextToken: string | null) => {
    setTokenState(nextToken);
    if (nextToken) {
      window.localStorage.setItem(TOKEN_KEY, nextToken);
    } else {
      window.localStorage.removeItem(TOKEN_KEY);
      setUserEmailState(null);
      window.localStorage.removeItem(USER_EMAIL_KEY);
    }
  };

  const value = useMemo(
    () => ({
      token,
      setToken,
      userEmail,
      setUserEmail,
      ready,
    }),
    [token, userEmail, ready]
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
