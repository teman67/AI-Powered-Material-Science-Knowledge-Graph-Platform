"use client";

import { FormEvent, useState } from "react";

import { PlatformShell } from "../components/platform-shell";
import { useAuth } from "../components/auth-provider";
import { ChatQueryResponse, queryChat } from "../../lib/api";

export default function ChatPage() {
  const { token } = useAuth();
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [result, setResult] = useState<ChatQueryResponse | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!token) {
      setMessage("Authenticate first to query the secured chat endpoint.");
      return;
    }

    if (!query.trim()) {
      setMessage("Enter a scientific question to query.");
      return;
    }

    setBusy(true);
    setMessage(null);
    try {
      const response = await queryChat(
        {
          query: query.trim(),
          top_k: topK,
        },
        token
      );
      setResult(response);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Chat query failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <PlatformShell
      title="Scientific Chat"
      subtitle="Ask material science questions and inspect retrieved semantic and graph evidence behind each answer."
    >
      <section className="stagger">
        <article className="panel-card">
          <h2>Ask a Question</h2>
          <form className="chat-form" onSubmit={handleSubmit}>
            <label>
              Question
              <textarea
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Which materials have high thermal conductivity and what applications are linked to them?"
                minLength={3}
                maxLength={4000}
                required
              />
            </label>

            <label>
              Top K chunks
              <input
                type="number"
                min={1}
                max={20}
                value={topK}
                onChange={(event) => setTopK(Math.max(1, Math.min(20, Number(event.target.value) || 5)))}
              />
            </label>

            <button type="submit" disabled={!token || busy}>
              {busy ? "Querying..." : "Query Chat"}
            </button>
          </form>

          {message ? <p className="info-line">{message}</p> : null}
        </article>

        {result ? (
          <>
            <article className="panel-card">
              <h2>Answer</h2>
              <p className="answer-text">{result.answer}</p>
            </article>

            <article className="panel-card">
              <h2>Semantic Contexts</h2>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Chunk</th>
                      <th>Document</th>
                      <th>Score</th>
                      <th>Excerpt</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.contexts.length === 0 ? (
                      <tr>
                        <td colSpan={4}>No semantic contexts returned.</td>
                      </tr>
                    ) : (
                      result.contexts.map((context) => (
                        <tr key={context.chunk_id}>
                          <td>{context.chunk_id}</td>
                          <td>{context.document_id}</td>
                          <td>{context.score.toFixed(3)}</td>
                          <td>{context.excerpt}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </article>

            <article className="panel-card">
              <h2>Graph Contexts</h2>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Source</th>
                      <th>Relation</th>
                      <th>Target</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.graph_contexts.length === 0 ? (
                      <tr>
                        <td colSpan={3}>No graph contexts returned.</td>
                      </tr>
                    ) : (
                      result.graph_contexts.map((context, index) => (
                        <tr key={`${context.source}-${context.relation}-${context.target}-${index}`}>
                          <td>{context.source}</td>
                          <td>{context.relation}</td>
                          <td>{context.target}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </article>
          </>
        ) : null}
      </section>
    </PlatformShell>
  );
}
