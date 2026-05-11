"use client";

import { useEffect, useMemo, useState } from "react";

import { useAuth } from "../components/auth-provider";
import { PlatformShell } from "../components/platform-shell";
import { DocumentDetailResponse, RdfExportResponse, exportRdf, listDocuments } from "../../lib/api";

function documentDisplayName(doc: DocumentDetailResponse): string {
  const title = (doc.title || "").trim();
  if (title) {
    return title;
  }

  const leaf = doc.file_path.split(/[\\/]/).pop() || `Document ${doc.id}`;
  return leaf.replace(/^[a-f0-9]{32}_/i, "");
}

export default function RdfPage() {
  const { token, ready } = useAuth();
  const [documentId, setDocumentId] = useState("");
  const [documents, setDocuments] = useState<DocumentDetailResponse[]>([]);
  const [result, setResult] = useState<RdfExportResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [loadingDocuments, setLoadingDocuments] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const selectedDocument = useMemo(() => {
    const numericId = Number(documentId);
    if (!numericId || Number.isNaN(numericId)) {
      return null;
    }
    return documents.find((doc) => doc.id === numericId) || null;
  }, [documentId, documents]);

  useEffect(() => {
    if (!ready) {
      return;
    }

    if (!token) {
      setDocuments([]);
      setDocumentId("");
      setResult(null);
      return;
    }

    let cancelled = false;
    setLoadingDocuments(true);
    listDocuments(200, token)
      .then((response) => {
        if (cancelled) {
          return;
        }

        const items = [...response.items].sort((a, b) => b.id - a.id);
        setDocuments(items);
        if (items.length === 0) {
          setDocumentId("");
          return;
        }

        setDocumentId((current) => {
          const exists = items.some((doc) => String(doc.id) === current);
          return exists ? current : String(items[0].id);
        });
      })
      .catch(() => {
        if (cancelled) {
          return;
        }
        setDocuments([]);
        setDocumentId("");
        setMessage("Could not load documents for RDF export.");
      })
      .finally(() => {
        if (!cancelled) {
          setLoadingDocuments(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [ready, token]);

  async function handleFetch() {
    if (!token) {
      setMessage("Authenticate first to export RDF.");
      return;
    }

    const numericId = Number(documentId);
    if (!numericId || Number.isNaN(numericId)) {
      setMessage("Select a document by name.");
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
          <div className="inline-form rdf-inline-form">
            <select
              value={documentId}
              onChange={(event) => setDocumentId(event.target.value)}
              disabled={!token || loadingDocuments || documents.length === 0}
            >
              {documents.length === 0 ? <option value="">No documents available</option> : null}
              {documents.map((doc) => (
                <option key={doc.id} value={String(doc.id)}>
                  {documentDisplayName(doc).slice(0, 90)} ({doc.status})
                </option>
              ))}
            </select>
            <button type="button" onClick={handleFetch} disabled={!token || busy || !documentId}>
              {busy ? "Generating..." : "Export RDF"}
            </button>
          </div>
          {selectedDocument ? (
            <p className="info-line">
              Selected: {documentDisplayName(selectedDocument)}
            </p>
          ) : null}
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
