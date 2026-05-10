"use client";

import { useState } from "react";

import { useAuth } from "../components/auth-provider";
import { PlatformShell } from "../components/platform-shell";
import { RdfExportResponse, exportRdf } from "../../lib/api";

export default function RdfPage() {
  const { token } = useAuth();
  const [documentId, setDocumentId] = useState("");
  const [result, setResult] = useState<RdfExportResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function handleFetch() {
    if (!token) {
      setMessage("Authenticate first to export RDF.");
      return;
    }

    const numericId = Number(documentId);
    if (!numericId || Number.isNaN(numericId)) {
      setMessage("Provide a numeric document ID.");
      return;
    }

    setBusy(true);
    setMessage(null);
    try {
      const payload = await exportRdf(numericId, token);
      setResult(payload);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "RDF export failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <PlatformShell
      title="RDF Viewer"
      subtitle="Generate ontology-aware triples on demand and inspect SHACL validation output from secured API endpoints."
    >
      <section className="stagger">
        <article className="panel-card">
          <h2>Export RDF for Document</h2>
          <div className="inline-form">
            <input
              type="number"
              min={1}
              value={documentId}
              onChange={(event) => setDocumentId(event.target.value)}
              placeholder="Document ID"
            />
            <button type="button" onClick={handleFetch} disabled={!token || busy}>
              {busy ? "Generating..." : "Export RDF"}
            </button>
          </div>
          {message ? <p className="info-line">{message}</p> : null}
        </article>

        {result ? (
          <>
            <article className="panel-card">
              <h2>Validation Summary</h2>
              <div className="stats-grid">
                <article className="stat-card">
                  <h3>{result.document_id}</h3>
                  <p>Document ID</p>
                </article>
                <article className="stat-card">
                  <h3>{result.entity_count}</h3>
                  <p>Extracted entities</p>
                </article>
                <article className="stat-card">
                  <h3>{result.is_valid ? "Valid" : "Invalid"}</h3>
                  <p>SHACL status</p>
                </article>
              </div>
            </article>

            <article className="panel-card">
              <div className="panel-row">
                <h2>Turtle RDF</h2>
                <button
                  type="button"
                  className="secondary"
                  onClick={async () => {
                    await navigator.clipboard.writeText(result.ttl_content);
                    setMessage("TTL copied to clipboard.");
                  }}
                >
                  Copy TTL
                </button>
              </div>
              <pre className="code-block">{result.ttl_content}</pre>
            </article>

            <article className="panel-card">
              <h2>SHACL Validation Report</h2>
              <pre className="code-block">{result.validation_report}</pre>
            </article>
          </>
        ) : null}
      </section>
    </PlatformShell>
  );
}
