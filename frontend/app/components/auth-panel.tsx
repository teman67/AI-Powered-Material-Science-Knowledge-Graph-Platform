"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import { loginUser, registerUser } from "../../lib/api";
import { useAuth } from "./auth-provider";

type Mode = "login" | "register";

export function AuthPanel() {
  const { token, setToken, ready } = useAuth();
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [messageTone, setMessageTone] = useState<"neutral" | "success" | "error">("neutral");
  const authenticated = Boolean(token);
  const wrapRef = useRef<HTMLDivElement>(null);

  const initials = useMemo(() => {
    return email ? email[0].toUpperCase() : "?";
  }, [email]);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleOutside(e: MouseEvent) {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", handleOutside);
    return () => document.removeEventListener("mousedown", handleOutside);
  }, [open]);

  // Close dropdown on successful auth
  useEffect(() => {
    if (authenticated) setOpen(false);
  }, [authenticated]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    setMessageTone("neutral");
    setBusy(true);
    try {
      if (mode === "register") {
        await registerUser({ email, password, full_name: fullName || undefined });
      }
      const loginResponse = await loginUser({ email, password });
      setToken(loginResponse.access_token);
      setMessage("Authenticated successfully.");
      setMessageTone("success");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Authentication failed.");
      setMessageTone("error");
    } finally {
      setBusy(false);
    }
  }

  function handleLogout() {
    setToken(null);
    setMessage(null);
  }

  if (!ready) {
    return (
      <div className="auth-topbar-loading">
        <span className="btn-spinner" />
      </div>
    );
  }

  /* ── Authenticated pill ── */
  if (authenticated) {
    return (
      <div className="auth-topbar-user">
        <span className="auth-topbar-live-dot" />
        <span className="auth-topbar-avatar">{initials}</span>
        <span className="auth-topbar-email">{email || "Researcher"}</span>
        <button type="button" className="auth-topbar-signout" onClick={handleLogout}>
          Sign Out
        </button>
      </div>
    );
  }

  /* ── Guest: trigger + dropdown ── */
  return (
    <div className="auth-topbar-wrap" ref={wrapRef}>
      <button
        type="button"
        className={`auth-topbar-trigger ${open ? "auth-trigger-open" : ""}`}
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="true"
        aria-expanded={open}
      >
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
          <circle cx="12" cy="7" r="4" />
        </svg>
        Sign In
        <svg className={`auth-chevron ${open ? "chevron-up" : ""}`} width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {open && (
        <div className="auth-dropdown">
          {/* Tabs */}
          <div className="auth-dropdown-tabs">
            <button
              type="button"
              className={`auth-dropdown-tab ${mode === "login" ? "auth-dropdown-tab-active" : ""}`}
              onClick={() => setMode("login")}
            >
              Sign In
            </button>
            <button
              type="button"
              className={`auth-dropdown-tab ${mode === "register" ? "auth-dropdown-tab-active" : ""}`}
              onClick={() => setMode("register")}
            >
              Register
            </button>
          </div>

          {/* Form */}
          <form className="auth-dropdown-form" onSubmit={handleSubmit}>
            <div className="auth-dropdown-field">
              <label htmlFor="auth-email">Email</label>
              <input
                id="auth-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="scientist@lab.org"
                required
                autoFocus
              />
            </div>

            {mode === "register" && (
              <div className="auth-dropdown-field">
                <label htmlFor="auth-name">Full Name</label>
                <input
                  id="auth-name"
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Research User"
                />
              </div>
            )}

            <div className="auth-dropdown-field">
              <label htmlFor="auth-password">Password</label>
              <input
                id="auth-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={8}
                required
              />
            </div>

            <button type="submit" className="auth-dropdown-submit" disabled={busy}>
              {busy ? (
                <><span className="btn-spinner" /> Working…</>
              ) : mode === "login" ? "→ Sign In" : "→ Register & Sign In"}
            </button>
          </form>

          {message && (
            <div className={`auth-dropdown-message auth-message-${messageTone}`}>
              <span className="msg-icon">
                {messageTone === "success" ? "✓" : messageTone === "error" ? "✕" : "·"}
              </span>
              {message}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
