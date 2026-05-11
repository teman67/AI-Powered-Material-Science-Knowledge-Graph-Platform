"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { PlatformShell } from "./components/platform-shell";
import { useAuth } from "./components/auth-provider";
import { DocumentDetailResponse, deleteDocument, getDocument, listDocuments, uploadDocument } from "../lib/api";

function sortDocs(items: DocumentDetailResponse[]) {
  return [...items].sort((a, b) => b.id - a.id);
}

export default function Home() {
  const { token, ready } = useAuth();
  const [docs, setDocs] = useState<DocumentDetailResponse[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [lookupId, setLookupId] = useState("");
  const [busy, setBusy] = useState(false);
  const [deletingDocumentId, setDeletingDocumentId] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const stats = useMemo(() => {
    const total = docs.length;
    const processed = docs.filter((doc) => doc.status === "processed").length;
    const processing = docs.filter((doc) => doc.status === "processing").length;
    const failed = docs.filter((doc) => doc.status === "failed").length;
    const chunks = docs.reduce((sum, doc) => sum + doc.chunk_count, 0);
    return { total, processed, processing, failed, chunks };
  }, [docs]);

  const completionRate = useMemo(() => {
    if (stats.total === 0) {
      return 0;
    }
    return Math.round((stats.processed / stats.total) * 100);
  }, [stats.processed, stats.total]);

  const failureRate = useMemo(() => {
    if (stats.total === 0) {
      return 0;
    }
    return Math.round((stats.failed / stats.total) * 100);
  }, [stats.failed, stats.total]);

  const loadDocuments = useCallback(async () => {
    if (!token) {
      setDocs([]);
      return;
    }

    const response = await listDocuments(150, token);
    setDocs(sortDocs(response.items));
  }, [token]);

  async function refreshDocument(documentId: number) {
    if (!token) {
      return;
    }
    const detail = await getDocument(documentId, token);
    setDocs((current) => {
      const withoutCurrent = current.filter((doc) => doc.id !== detail.id);
      return sortDocs([...withoutCurrent, detail]);
    });
  }

  useEffect(() => {
    if (!ready) {
      return;
    }

    if (!token) {
      setMessage(null);
    }

    loadDocuments().catch(() => {
      setMessage("Could not load document list.");
    });
  }, [ready, token, loadDocuments]);

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !selectedFile) {
      setMessage("Sign in and select a PDF before uploading.");
      return;
    }

    setBusy(true);
    setMessage(null);
    try {
      const result = await uploadDocument(selectedFile, token);
      await loadDocuments();
      setSelectedFile(null);
      setMessage(`Uploaded document ${result.document_id} with status ${result.status}.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Upload failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleLookup() {
    if (!token) {
      setMessage("Authenticate first to query document status.");
      return;
    }

    const numericId = Number(lookupId);
    if (!numericId || Number.isNaN(numericId)) {
      setMessage("Enter a numeric document ID.");
      return;
    }

    setBusy(true);
    setMessage(null);
    try {
      await refreshDocument(numericId);
      setMessage(`Tracked document ${numericId}.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not fetch document details.");
    } finally {
      setBusy(false);
    }
  }

  async function handleDeleteDocument(documentId: number) {
    if (!token) {
      setMessage("Authenticate first to delete documents.");
      return;
    }

    const approved = window.confirm(`Delete document ${documentId}? This removes chunks, RDF, extracted entities, and graph references.`);
    if (!approved) {
      return;
    }

    setDeletingDocumentId(documentId);
    setMessage(null);
    try {
      const result = await deleteDocument(documentId, token);
      setDocs((current) => current.filter((doc) => doc.id !== documentId));
      const fileState = result.file_deleted ? "file removed" : "file already missing";
      const graphState = result.graph_cleanup_applied ? "graph cleaned" : "graph cleanup skipped";
      setMessage(`Deleted document ${documentId} (${fileState}, ${graphState}).`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to delete document.");
    } finally {
      setDeletingDocumentId(null);
    }
  }

  return (
    <PlatformShell
      title="Dashboard"
      subtitle="Upload papers, track ingestion state, and monitor extraction health against secured backend APIs."
    >
      <section className="stagger">
        <article className="panel-card dashboard-hero">
          <div className="dashboard-hero-main">
            <p className="eyebrow">Pipeline Control Room</p>
            <h2>Material Paper Ingestion Hub</h2>
            <p className="muted">
              Keep the ingestion queue healthy, follow processing outcomes, and refresh any document state in one place.
            </p>
          </div>
          <div className="dashboard-hero-side">
            <div className="dashboard-metric">
              <span>Completion Rate</span>
              <strong>{completionRate}%</strong>
            </div>
            <div className="dashboard-metric">
              <span>Failure Rate</span>
              <strong>{failureRate}%</strong>
            </div>
            <div className="dashboard-metric">
              <span>Chunk Footprint</span>
              <strong>{stats.chunks}</strong>
            </div>
          </div>
        </article>

        <div className="stats-grid">
          <article className="stat-card">
            <h3>{stats.total}</h3>
            <p>Tracked documents</p>
          </article>
          <article className="stat-card">
            <h3>{stats.processed}</h3>
            <p>Processed</p>
          </article>
          <article className="stat-card">
            <h3>{stats.processing}</h3>
            <p>Processing</p>
          </article>
          <article className="stat-card">
            <h3>{stats.failed}</h3>
            <p>Failed</p>
          </article>
          <article className="stat-card">
            <h3>{stats.chunks}</h3>
            <p>Total indexed chunks</p>
          </article>
        </div>

        <div className="action-grid">
          <article className="panel-card">
            <h2>Upload PDF</h2>
            <form className="inline-form" onSubmit={handleUpload}>
              <input
                type="file"
                accept="application/pdf"
                onChange={(event) => setSelectedFile(event.target.files?.[0] || null)}
              />
              <button type="submit" disabled={!ready || !token || busy || !selectedFile}>
                {busy ? "Uploading..." : "Upload Document"}
              </button>
            </form>
            <p className="muted">{selectedFile ? `Selected: ${selectedFile.name}` : "Choose a materials-science PDF to start extraction."}</p>
          </article>

          <article className="panel-card">
            <h2>Track Existing Document</h2>
            <div className="inline-form">
              <input
                type="number"
                min={1}
                value={lookupId}
                onChange={(event) => setLookupId(event.target.value)}
                placeholder="Document ID"
              />
              <button type="button" onClick={handleLookup} disabled={!ready || !token || busy}>
                Refresh by ID
              </button>
            </div>
            <p className="muted">Quickly sync one document without refreshing the full dashboard table.</p>
          </article>
        </div>

        {message ? <p className="info-line">{message}</p> : null}

        <article className="panel-card">
          <div className="panel-row">
            <h2>Tracked Papers</h2>
            <button
              type="button"
              className="secondary"
              disabled={!token || docs.length === 0 || busy}
              onClick={async () => {
                if (!token) {
                  return;
                }
                setBusy(true);
                try {
                  await loadDocuments();
                } finally {
                  setBusy(false);
                }
              }}
            >
              Refresh All
            </button>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Title</th>
                  <th>Status</th>
                  <th>Chunks</th>
                  <th>Uploaded</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {docs.length === 0 ? (
                  <tr>
                    <td colSpan={6}>No tracked documents yet. Upload or lookup by ID.</td>
                  </tr>
                ) : (
                  docs.map((doc) => (
                    <tr key={doc.id}>
                      <td>{doc.id}</td>
                      <td>{doc.title || "Untitled"}</td>
                      <td>
                        <span className={`status-badge status-${doc.status}`}>{doc.status}</span>
                      </td>
                      <td>{doc.chunk_count}</td>
                      <td>{new Date(doc.upload_date).toLocaleString()}</td>
                      <td>
                        <div className="row-actions">
                          <button
                            type="button"
                            className="danger"
                            disabled={!token || busy || deletingDocumentId === doc.id}
                            onClick={() => handleDeleteDocument(doc.id)}
                          >
                            {deletingDocumentId === doc.id ? "Deleting..." : "Delete"}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </article>
      </section>
    </PlatformShell>
  );
}
