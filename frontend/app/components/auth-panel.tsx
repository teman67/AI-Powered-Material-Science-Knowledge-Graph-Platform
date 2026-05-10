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
  const tokenPreview = useMemo(() => {
    if (!token) {
      return "Not authenticated";
    }
    return `${token.slice(0, 14)}...`;
  }, [token]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
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
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Authentication failed.");
    } finally {
      setBusy(false);
    }
  }

  if (!ready) {
    return <p className="auth-note">Loading session...</p>;
  }

  return (
    <section className="auth-panel">
      <div className="auth-header-row">
        <h2>Secure Session</h2>
        <span className={`status-badge ${token ? "status-ok" : "status-warn"}`}>{token ? "Connected" : "No token"}</span>
      </div>

      <p className="auth-note">Token preview: {tokenPreview}</p>

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
            onClick={() => {
              setToken(null);
              setMessage("Session token removed.");
            }}
          >
            Sign out
          </button>
        </div>
      </form>

      {message ? <p className="auth-note">{message}</p> : null}
    </section>
  );
}
