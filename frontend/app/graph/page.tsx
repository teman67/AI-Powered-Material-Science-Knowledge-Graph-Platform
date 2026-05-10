"use client";

import { useMemo, useState } from "react";

import { useAuth } from "../components/auth-provider";
import { PlatformShell } from "../components/platform-shell";
import { GraphRelationItem, getGraphMaterials, getGraphRelations } from "../../lib/api";

type NodePoint = {
  label: string;
  x: number;
  y: number;
};

function buildNodePoints(relations: GraphRelationItem[]): NodePoint[] {
  const labels = Array.from(new Set(relations.flatMap((row) => [row.source, row.target]))).slice(0, 20);
  if (labels.length === 0) {
    return [];
  }

  const center = 220;
  const radius = 160;
  return labels.map((label, index) => {
    const angle = (index / labels.length) * Math.PI * 2;
    return {
      label,
      x: center + Math.cos(angle) * radius,
      y: center + Math.sin(angle) * radius,
    };
  });
}

export default function GraphPage() {
  const { token } = useAuth();
  const [materials, setMaterials] = useState<{ material: string; property_count: number; process_count: number; application_count: number }[]>([]);
  const [relations, setRelations] = useState<GraphRelationItem[]>([]);
  const [materialFilter, setMaterialFilter] = useState("");
  const [materialLimit, setMaterialLimit] = useState(30);
  const [relationLimit, setRelationLimit] = useState(80);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const nodePoints = useMemo(() => buildNodePoints(relations), [relations]);
  const indexByLabel = useMemo(() => {
    return new Map(nodePoints.map((node) => [node.label, node]));
  }, [nodePoints]);

  async function loadGraphData() {
    if (!token) {
      setError("Authenticate first to access graph endpoints.");
      return;
    }

    setBusy(true);
    setError(null);
    try {
      const [materialResponse, relationResponse] = await Promise.all([
        getGraphMaterials(materialLimit, token),
        getGraphRelations(relationLimit, materialFilter || undefined, token),
      ]);
      setMaterials(materialResponse.items);
      setRelations(relationResponse.items);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Failed to load graph data.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <PlatformShell
      title="Graph View"
      subtitle="Inspect material-property-process relations from Neo4j with secured retrieval and filter controls."
    >
      <section className="stagger">
        <article className="panel-card">
          <h2>Graph Retrieval Controls</h2>
          <div className="inline-form three-col">
            <label>
              Materials limit
              <input
                type="number"
                min={1}
                max={200}
                value={materialLimit}
                onChange={(event) => setMaterialLimit(Number(event.target.value) || 30)}
              />
            </label>
            <label>
              Relations limit
              <input
                type="number"
                min={1}
                max={500}
                value={relationLimit}
                onChange={(event) => setRelationLimit(Number(event.target.value) || 80)}
              />
            </label>
            <label>
              Material filter
              <input
                type="text"
                value={materialFilter}
                onChange={(event) => setMaterialFilter(event.target.value)}
                placeholder="Optional material name"
              />
            </label>
          </div>
          <div className="panel-row">
            <button type="button" onClick={loadGraphData} disabled={!token || busy}>
              {busy ? "Loading..." : "Load Graph"}
            </button>
            <span className="muted">{relations.length} relations, {materials.length} materials</span>
          </div>
          {error ? <p className="info-line">{error}</p> : null}
        </article>

        <article className="panel-card">
          <h2>Relation Graph Snapshot</h2>
          <div className="graph-canvas">
            {nodePoints.length === 0 ? (
              <p className="muted">Load graph data to render the relation snapshot.</p>
            ) : (
              <svg viewBox="0 0 440 440" role="img" aria-label="Material relation graph">
                {relations.slice(0, 80).map((edge, index) => {
                  const source = indexByLabel.get(edge.source);
                  const target = indexByLabel.get(edge.target);
                  if (!source || !target) {
                    return null;
                  }
                  return (
                    <line
                      key={`${edge.source}-${edge.target}-${index}`}
                      x1={source.x}
                      y1={source.y}
                      x2={target.x}
                      y2={target.y}
                      className="graph-edge"
                    />
                  );
                })}
                {nodePoints.map((node) => (
                  <g key={node.label}>
                    <circle cx={node.x} cy={node.y} r="11" className="graph-node" />
                    <text x={node.x} y={node.y - 15} textAnchor="middle" className="graph-label">
                      {node.label.slice(0, 14)}
                    </text>
                  </g>
                ))}
              </svg>
            )}
          </div>
        </article>

        <article className="panel-card">
          <h2>Top Materials</h2>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Material</th>
                  <th>Properties</th>
                  <th>Processes</th>
                  <th>Applications</th>
                </tr>
              </thead>
              <tbody>
                {materials.length === 0 ? (
                  <tr>
                    <td colSpan={4}>No materials loaded.</td>
                  </tr>
                ) : (
                  materials.map((row) => (
                    <tr key={row.material}>
                      <td>{row.material}</td>
                      <td>{row.property_count}</td>
                      <td>{row.process_count}</td>
                      <td>{row.application_count}</td>
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
