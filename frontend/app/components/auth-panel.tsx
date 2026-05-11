"use client";

import { FormEvent, useMemo, useState } from "react";

import { loginUser, registerUser } from "../../lib/api";
import { useAuth } from "./auth-provider";

type Mode = "login" | "register";

export function AuthPanel() {
  const { token, setToken, ready } = useAuth();
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [messageTone, setMessageTone] = useState<"neutral" | "success" | "error">("neutral");
  const authenticated = Boolean(token);
  const tokenPreview = useMemo(() => {
    if (!token) {
      return "Not authenticated";
    }
    return `${token.slice(0, 12)}...${token.slice(-10)}`;
  }, [token]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    setMessageTone("neutral");
    setBusy(true);
    try {
      if (mode === "register") {
        await registerUser({
          email,
          password,
          full_name: fullName || undefined,
        });
      }

      const loginResponse = await loginUser({ email, password });
      setToken(loginResponse.access_token);
      setMessage("Authenticated with backend.");
      setMessageTone("success");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Authentication failed.");
      setMessageTone("error");
    } finally {
      setBusy(false);
    }
  }

  if (!ready) {
    return <p className="auth-note">Loading session...</p>;
  }

  return (
    <section className="auth-panel auth-panel-modern">
      <div className="auth-header-row">
        <div>
          <p className="auth-eyebrow">Identity Gateway</p>
          <h2>Secure Session</h2>
        </div>
        <span className={`status-badge ${token ? "status-ok" : "status-warn"}`}>{token ? "Connected" : "Guest"}</span>
      </div>

      <div className="session-card">
        <p className="auth-note">Token fingerprint</p>
        <p className="token-preview">{tokenPreview}</p>
      </div>

      <p className="auth-note">
        {authenticated
          ? "Your session token is active. You can continue securely or switch accounts."
          : "Sign in to unlock upload, chat, graph, and RDF endpoints."}
      </p>

      <div className="mode-switch">
        <button
          type="button"
          className={mode === "login" ? "active" : ""}
          onClick={() => setMode("login")}
        >
          Login
        </button>
        <button
          type="button"
          className={mode === "register" ? "active" : ""}
          onClick={() => setMode("register")}
        >
          Register + Login
        </button>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="scientist@lab.org"
            required
          />
        </label>

        {mode === "register" ? (
          <label>
            Full name
            <input
              type="text"
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              placeholder="Research User"
            />
          </label>
        ) : null}

        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            minLength={8}
            required
          />
        </label>

        <div className="auth-actions">
          <button type="submit" disabled={busy}>
            {busy ? "Working..." : mode === "login" ? "Login" : "Register + Login"}
          </button>
          <button
            type="button"
            className="secondary"
            disabled={!token}
            onClick={() => {
              setToken(null);
              setMessage("Session token removed.");
              setMessageTone("neutral");
            }}
          >
            Logout
          </button>
        </div>
      </form>

      {message ? <p className={`auth-note auth-feedback auth-feedback-${messageTone}`}>{message}</p> : null}
    </section>
  );
}
