"use client";

import { useMemo, useState } from "react";

import { useAuth } from "../components/auth-provider";
import { PlatformShell } from "../components/platform-shell";
import {
  CrossPaperExplorationItem,
  CrossPaperLinkItem,
  CrossPaperRecommendationEdge,
  CrossPaperRecommendationItem,
  GraphRelationItem,
  getCrossPaperExploration,
  getCrossPaperLinks,
  getCrossPaperRecommendations,
  getGraphMaterials,
  getGraphRelations,
} from "../../lib/api";

type NodePoint = {
  label: string;
  x: number;
  y: number;
};

type DocumentGraphNode = {
  id: number;
  label: string;
  score: number;
};

type DocumentNodePoint = {
  id: number;
  label: string;
  score: number;
  x: number;
  y: number;
};

type RecommendationGraphData = {
  nodes: DocumentGraphNode[];
  edges: CrossPaperRecommendationEdge[];
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

function buildRecommendationGraph(
  recommendations: CrossPaperRecommendationItem[],
  edges: CrossPaperRecommendationEdge[],
  minEdgeScore: number,
  centerDocumentId: number,
  hops: number,
): RecommendationGraphData {
  const nodeById = new Map<number, DocumentGraphNode>();
  for (const item of recommendations) {
    const sourceLabel = item.source_document_title || `Document ${item.source_document_id}`;
    const targetLabel = item.target_document_title || `Document ${item.target_document_id}`;
    const sourceExisting = nodeById.get(item.source_document_id);
    const targetExisting = nodeById.get(item.target_document_id);

    nodeById.set(item.source_document_id, {
      id: item.source_document_id,
      label: sourceLabel,
      score: Math.max(item.score, sourceExisting?.score || 0),
    });
    nodeById.set(item.target_document_id, {
      id: item.target_document_id,
      label: targetLabel,
      score: Math.max(item.score, targetExisting?.score || 0),
    });
  }

  if (nodeById.size === 0) {
    return { nodes: [], edges: [] };
  }

  const eligibleEdges = edges.filter((edge) => edge.score >= minEdgeScore);

  if (centerDocumentId <= 0 || !nodeById.has(centerDocumentId)) {
    const sortedNodes = Array.from(nodeById.values())
      .sort((left, right) => right.score - left.score)
      .slice(0, 30);
    const allowedNodeIds = new Set(sortedNodes.map((node) => node.id));
    return {
      nodes: sortedNodes,
      edges: eligibleEdges.filter((edge) => allowedNodeIds.has(edge.source_document_id) && allowedNodeIds.has(edge.target_document_id)),
    };
  }

  const adjacency = new Map<number, Set<number>>();
  for (const edge of eligibleEdges) {
    adjacency.set(edge.source_document_id, (adjacency.get(edge.source_document_id) || new Set()).add(edge.target_document_id));
    adjacency.set(edge.target_document_id, (adjacency.get(edge.target_document_id) || new Set()).add(edge.source_document_id));
  }

  const maxHops = Math.max(1, hops);
  const visible = new Set<number>([centerDocumentId]);
  let frontier = new Set<number>([centerDocumentId]);

  for (let depth = 0; depth < maxHops; depth += 1) {
    const next = new Set<number>();
    for (const nodeId of frontier) {
      const neighbors = adjacency.get(nodeId);
      if (!neighbors) {
        continue;
      }
      for (const neighborId of neighbors) {
        if (!visible.has(neighborId)) {
          visible.add(neighborId);
          next.add(neighborId);
        }
      }
    }
    frontier = next;
    if (frontier.size === 0) {
      break;
    }
  }

  const nodes = Array.from(nodeById.values()).filter((node) => visible.has(node.id));
  const visibleEdges = eligibleEdges.filter((edge) => visible.has(edge.source_document_id) && visible.has(edge.target_document_id));
  nodes.sort((left, right) => right.score - left.score);

  return {
    nodes: nodes.slice(0, 30),
    edges: visibleEdges,
  };
}

function buildDocumentNodePoints(nodes: DocumentGraphNode[]): DocumentNodePoint[] {
  if (nodes.length === 0) {
    return [];
  }

  const center = 250;
  const radius = nodes.length === 1 ? 0 : Math.min(210, 100 + nodes.length * 5);
  return nodes.map((node, index) => {
    const angle = (index / nodes.length) * Math.PI * 2;
    return {
      id: node.id,
      label: node.label,
      score: node.score,
      x: center + Math.cos(angle) * radius,
      y: center + Math.sin(angle) * radius,
    };
  });
}

export default function GraphPage() {
  const { token } = useAuth();
  const [materials, setMaterials] = useState<{ material: string; property_count: number; process_count: number; application_count: number }[]>([]);
  const [relations, setRelations] = useState<GraphRelationItem[]>([]);
  const [crossPaperLinks, setCrossPaperLinks] = useState<CrossPaperLinkItem[]>([]);
  const [crossPaperExploration, setCrossPaperExploration] = useState<CrossPaperExplorationItem[]>([]);
  const [recommendations, setRecommendations] = useState<CrossPaperRecommendationItem[]>([]);
  const [recommendationEdges, setRecommendationEdges] = useState<CrossPaperRecommendationEdge[]>([]);
  const [materialFilter, setMaterialFilter] = useState("");
  const [materialLimit, setMaterialLimit] = useState(30);
  const [relationLimit, setRelationLimit] = useState(80);
  const [crossPaperLimit, setCrossPaperLimit] = useState(20);
  const [minSharedEntities, setMinSharedEntities] = useState(2);
  const [explorationDocumentId, setExplorationDocumentId] = useState(0);
  const [explorationQuery, setExplorationQuery] = useState("");
  const [recommendationQuery, setRecommendationQuery] = useState("");
  const [recommendationSeedLimit, setRecommendationSeedLimit] = useState(5);
  const [expansionCenterDocumentId, setExpansionCenterDocumentId] = useState(0);
  const [expansionHops, setExpansionHops] = useState(2);
  const [expansionMinEdgeScore, setExpansionMinEdgeScore] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const nodePoints = useMemo(() => buildNodePoints(relations), [relations]);
  const indexByLabel = useMemo(() => {
    return new Map(nodePoints.map((node) => [node.label, node]));
  }, [nodePoints]);

  const recommendationGraph = useMemo(
    () => buildRecommendationGraph(recommendations, recommendationEdges, expansionMinEdgeScore, expansionCenterDocumentId, expansionHops),
    [recommendations, recommendationEdges, expansionMinEdgeScore, expansionCenterDocumentId, expansionHops],
  );

  const recommendationNodePoints = useMemo(
    () => buildDocumentNodePoints(recommendationGraph.nodes),
    [recommendationGraph.nodes],
  );

  const recommendationPointById = useMemo(
    () => new Map(recommendationNodePoints.map((node) => [node.id, node])),
    [recommendationNodePoints],
  );

  async function loadGraphData() {
    if (!token) {
      setError("Authenticate first to access graph endpoints.");
      return;
    }

    setBusy(true);
    setError(null);
    try {
      const explorationPromise = explorationDocumentId > 0
        ? getCrossPaperExploration(explorationDocumentId, crossPaperLimit, minSharedEntities, explorationQuery || undefined, token)
        : Promise.resolve({ items: [] as CrossPaperExplorationItem[] });

      const recommendationPromise = recommendationQuery.trim().length >= 2
        ? getCrossPaperRecommendations(recommendationQuery.trim(), crossPaperLimit, recommendationSeedLimit, minSharedEntities, token)
        : Promise.resolve({ query: recommendationQuery, items: [] as CrossPaperRecommendationItem[], edges: [] as CrossPaperRecommendationEdge[] });

      const [materialResponse, relationResponse, crossPaperResponse, explorationResponse, recommendationResponse] = await Promise.all([
        getGraphMaterials(materialLimit, token),
        getGraphRelations(relationLimit, materialFilter || undefined, token),
        getCrossPaperLinks(crossPaperLimit, minSharedEntities, token),
        explorationPromise,
        recommendationPromise,
      ]);
      setMaterials(materialResponse.items);
      setRelations(relationResponse.items);
      setCrossPaperLinks(crossPaperResponse.items);
      setCrossPaperExploration(explorationResponse.items);
      setRecommendations(recommendationResponse.items);
      setRecommendationEdges(recommendationResponse.edges);
      setExpansionCenterDocumentId((existing) => existing || recommendationResponse.items[0]?.source_document_id || 0);
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
            <label>
              Cross-paper links limit
              <input
                type="number"
                min={1}
                max={500}
                value={crossPaperLimit}
                onChange={(event) => setCrossPaperLimit(Number(event.target.value) || 20)}
              />
            </label>
            <label>
              Min shared entities
              <input
                type="number"
                min={1}
                max={20}
                value={minSharedEntities}
                onChange={(event) => setMinSharedEntities(Number(event.target.value) || 2)}
              />
            </label>
            <label>
              Explore from document ID
              <input
                type="number"
                min={0}
                max={1000000}
                value={explorationDocumentId}
                onChange={(event) => setExplorationDocumentId(Number(event.target.value) || 0)}
                placeholder="0 disables"
              />
            </label>
            <label>
              Exploration query (optional)
              <input
                type="text"
                value={explorationQuery}
                onChange={(event) => setExplorationQuery(event.target.value)}
                placeholder="e.g. thermal conductivity applications"
              />
            </label>
            <label>
              Recommendation query
              <input
                type="text"
                value={recommendationQuery}
                onChange={(event) => setRecommendationQuery(event.target.value)}
                placeholder="e.g. recommend papers for MoS2 synthesis"
              />
            </label>
            <label>
              Recommendation seed docs
              <input
                type="number"
                min={1}
                max={20}
                value={recommendationSeedLimit}
                onChange={(event) => setRecommendationSeedLimit(Number(event.target.value) || 5)}
              />
            </label>
            <label>
              Expansion center document ID
              <input
                type="number"
                min={0}
                max={1000000}
                value={expansionCenterDocumentId}
                onChange={(event) => setExpansionCenterDocumentId(Number(event.target.value) || 0)}
              />
            </label>
            <label>
              Expansion hops
              <input
                type="number"
                min={1}
                max={4}
                value={expansionHops}
                onChange={(event) => setExpansionHops(Math.max(1, Number(event.target.value) || 2))}
              />
            </label>
            <label>
              Expansion min edge score
              <input
                type="number"
                min={0}
                max={100}
                step="0.1"
                value={expansionMinEdgeScore}
                onChange={(event) => setExpansionMinEdgeScore(Number(event.target.value) || 0)}
              />
            </label>
          </div>
          <div className="panel-row">
            <button type="button" onClick={loadGraphData} disabled={!token || busy}>
              {busy ? "Loading..." : "Load Graph"}
            </button>
            <span className="muted">
              {relations.length} relations, {materials.length} materials, {crossPaperLinks.length} cross-paper links, {crossPaperExploration.length} exploration paths, {recommendations.length} recommendations
            </span>
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

        <article className="panel-card">
          <h2>Cross-Paper Knowledge Links</h2>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Document A</th>
                  <th>Document B</th>
                  <th>Shared Entities</th>
                  <th>Examples</th>
                </tr>
              </thead>
              <tbody>
                {crossPaperLinks.length === 0 ? (
                  <tr>
                    <td colSpan={4}>No cross-paper links found with current threshold.</td>
                  </tr>
                ) : (
                  crossPaperLinks.map((link) => (
                    <tr key={`${link.document_a_id}-${link.document_b_id}`}>
                      <td>
                        #{link.document_a_id} {link.document_a_title || "Untitled"}
                      </td>
                      <td>
                        #{link.document_b_id} {link.document_b_title || "Untitled"}
                      </td>
                      <td>{link.shared_entity_count}</td>
                      <td>{link.shared_entities.join(", ")}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </article>

        <article className="panel-card">
          <h2>Cross-Paper Exploration Paths</h2>
          <p className="muted">Set a source document ID in controls to traverse to related papers via shared entities.</p>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Path</th>
                  <th>Shared</th>
                  <th>Relevance</th>
                  <th>Bridge Entities</th>
                </tr>
              </thead>
              <tbody>
                {crossPaperExploration.length === 0 ? (
                  <tr>
                    <td colSpan={4}>No exploration paths loaded.</td>
                  </tr>
                ) : (
                  crossPaperExploration.map((item) => (
                    <tr key={`${item.source_document_id}-${item.target_document_id}`}>
                      <td>
                        #{item.source_document_id} {item.source_document_title || "Untitled"} → #{item.target_document_id} {item.target_document_title || "Untitled"}
                      </td>
                      <td>{item.shared_entity_count}</td>
                      <td>{item.relevance_score.toFixed(2)}</td>
                      <td>{item.bridge_entities.join(", ")}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </article>

        <article className="panel-card">
          <h2>Query-Native Recommendations</h2>
          <p className="muted">Provide a recommendation query to rank source-target document paths using query intent and shared entities.</p>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Recommendation Path</th>
                  <th>Score</th>
                  <th>Shared</th>
                  <th>Bridge Entities</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {recommendations.length === 0 ? (
                  <tr>
                    <td colSpan={5}>No recommendations loaded. Enter a recommendation query and click Load Graph.</td>
                  </tr>
                ) : (
                  recommendations.map((item) => (
                    <tr key={`${item.source_document_id}-${item.target_document_id}-${item.score}`}>
                      <td>
                        #{item.source_document_id} {item.source_document_title || "Untitled"} → #{item.target_document_id} {item.target_document_title || "Untitled"}
                      </td>
                      <td>{item.score.toFixed(2)}</td>
                      <td>{item.shared_entity_count}</td>
                      <td>{item.bridge_entities.join(", ")}</td>
                      <td>
                        <button
                          type="button"
                          onClick={() => {
                            setExpansionCenterDocumentId(item.source_document_id);
                            setExplorationDocumentId(item.source_document_id);
                          }}
                        >
                          Expand
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </article>

        <article className="panel-card">
          <h2>Interactive Recommendation Expansion</h2>
          <p className="muted">Click nodes to change expansion center. Hops and min edge score controls are in Graph Retrieval Controls.</p>
          <div className="graph-canvas">
            {recommendationNodePoints.length === 0 ? (
              <p className="muted">Load recommendations to render interactive expansion.</p>
            ) : (
              <svg viewBox="0 0 500 500" role="img" aria-label="Recommendation expansion graph">
                {recommendationGraph.edges.map((edge, index) => {
                  const source = recommendationPointById.get(edge.source_document_id);
                  const target = recommendationPointById.get(edge.target_document_id);
                  if (!source || !target) {
                    return null;
                  }
                  return (
                    <line
                      key={`${edge.source_document_id}-${edge.target_document_id}-${index}`}
                      x1={source.x}
                      y1={source.y}
                      x2={target.x}
                      y2={target.y}
                      className="graph-edge"
                      style={{ strokeWidth: Math.max(1, Math.min(4, edge.score / 3)) }}
                    />
                  );
                })}
                {recommendationNodePoints.map((node) => {
                  const isCenter = node.id === expansionCenterDocumentId;
                  return (
                    <g
                      key={node.id}
                      onClick={() => {
                        setExpansionCenterDocumentId(node.id);
                        setExplorationDocumentId(node.id);
                      }}
                    >
                      <circle
                        cx={node.x}
                        cy={node.y}
                        r={isCenter ? 13 : 10}
                        className="graph-node"
                        style={isCenter ? { fill: "#f6c85f" } : undefined}
                      />
                      <text x={node.x} y={node.y - 15} textAnchor="middle" className="graph-label">
                        {`#${node.id} ${node.label}`.slice(0, 18)}
                      </text>
                    </g>
                  );
                })}
              </svg>
            )}
          </div>
        </article>
      </section>
    </PlatformShell>
  );
}
