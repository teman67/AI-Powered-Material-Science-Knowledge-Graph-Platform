const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

type RequestOptions = {
  method?: "GET" | "POST" | "DELETE";
  token?: string | null;
  body?: Record<string, unknown> | FormData;
};

export type RegisterRequest = {
  email: string;
  password: string;
  full_name?: string;
};

export type UserResponse = {
  id: number;
  email: string;
  full_name: string | null;
  created_at: string;
};

export type LoginRequest = {
  email: string;
  password: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
  expires_in: number;
};

export type DocumentUploadResponse = {
  document_id: number;
  status: string;
  title: string | null;
  chunk_count: number;
};

export type DocumentDetailResponse = {
  id: number;
  title: string | null;
  status: string;
  file_path: string;
  upload_date: string;
  chunk_count: number;
};

export type DocumentListResponse = {
  items: DocumentDetailResponse[];
};

export type DocumentDeleteResponse = {
  document_id: number;
  file_deleted: boolean;
  graph_cleanup_applied: boolean;
};

export type GraphMaterialItem = {
  material: string;
  property_count: number;
  process_count: number;
  application_count: number;
};

export type GraphMaterialsResponse = {
  items: GraphMaterialItem[];
};

export type GraphRelationItem = {
  source: string;
  relation: string;
  target: string;
};

export type GraphRelationsResponse = {
  items: GraphRelationItem[];
};

export type CrossPaperLinkItem = {
  document_a_id: number;
  document_a_title: string | null;
  document_b_id: number;
  document_b_title: string | null;
  shared_entity_count: number;
  shared_entities: string[];
};

export type CrossPaperLinksResponse = {
  items: CrossPaperLinkItem[];
};

export type CrossPaperExplorationItem = {
  source_document_id: number;
  source_document_title: string | null;
  target_document_id: number;
  target_document_title: string | null;
  shared_entity_count: number;
  bridge_entities: string[];
  relevance_score: number;
};

export type CrossPaperExplorationResponse = {
  items: CrossPaperExplorationItem[];
};

export type CrossPaperRecommendationItem = {
  source_document_id: number;
  source_document_title: string | null;
  target_document_id: number;
  target_document_title: string | null;
  shared_entity_count: number;
  bridge_entities: string[];
  score: number;
};

export type CrossPaperRecommendationEdge = {
  source_document_id: number;
  target_document_id: number;
  shared_entity_count: number;
  score: number;
};

export type CrossPaperRecommendationsResponse = {
  query: string;
  items: CrossPaperRecommendationItem[];
  edges: CrossPaperRecommendationEdge[];
};

export type RdfExportResponse = {
  document_id: number;
  is_valid: boolean;
  entity_count: number;
  ttl_content: string;
  validation_report: string;
};

export type ChatQueryRequest = {
  query: string;
  top_k?: number;
};

export type ChatContext = {
  chunk_id: number;
  document_id: number;
  score: number;
  excerpt: string;
};

export type ChatGraphContext = {
  source: string;
  relation: string;
  target: string;
};

export type ChatQueryResponse = {
  answer: string;
  contexts: ChatContext[];
  graph_contexts: ChatGraphContext[];
};

async function requestJson<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
  };

  if (options.token) {
    headers.Authorization = `Bearer ${options.token}`;
  }

  let payload: BodyInit | undefined;
  if (options.body instanceof FormData) {
    payload = options.body;
  } else if (options.body) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(options.body);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method || "GET",
    headers,
    body: payload,
    cache: "no-store",
  });

  if (!response.ok) {
    const fallback = `${response.status} ${response.statusText}`;
    let detailMessage = fallback;
    try {
      const data = (await response.json()) as { detail?: string };
      if (data.detail) {
        detailMessage = data.detail;
      }
    } catch {
      detailMessage = fallback;
    }
    throw new Error(detailMessage);
  }

  return (await response.json()) as T;
}

export function registerUser(payload: RegisterRequest): Promise<UserResponse> {
  return requestJson<UserResponse>("/auth/register", {
    method: "POST",
    body: payload,
  });
}

export function loginUser(payload: LoginRequest): Promise<TokenResponse> {
  return requestJson<TokenResponse>("/auth/login", {
    method: "POST",
    body: payload,
  });
}

export function uploadDocument(file: File, token: string): Promise<DocumentUploadResponse> {
  const form = new FormData();
  form.append("file", file);
  return requestJson<DocumentUploadResponse>("/documents/upload", {
    method: "POST",
    token,
    body: form,
  });
}

export function getDocument(documentId: number, token: string): Promise<DocumentDetailResponse> {
  return requestJson<DocumentDetailResponse>(`/documents/${documentId}`, { token });
}

export function listDocuments(limit: number, token: string): Promise<DocumentListResponse> {
  return requestJson<DocumentListResponse>(`/documents?limit=${limit}`, { token });
}

export function deleteDocument(documentId: number, token: string): Promise<DocumentDeleteResponse> {
  return requestJson<DocumentDeleteResponse>(`/documents/${documentId}`, {
    method: "DELETE",
    token,
  });
}

export function getGraphMaterials(limit: number, token: string): Promise<GraphMaterialsResponse> {
  return requestJson<GraphMaterialsResponse>(`/graph/materials?limit=${limit}`, { token });
}

export function getGraphRelations(limit: number, material: string | undefined, token: string): Promise<GraphRelationsResponse> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (material) {
    params.set("material", material);
  }
  return requestJson<GraphRelationsResponse>(`/graph/relations?${params.toString()}`, { token });
}

export function getCrossPaperLinks(limit: number, minShared: number, token: string): Promise<CrossPaperLinksResponse> {
  const params = new URLSearchParams({
    limit: String(limit),
    min_shared: String(minShared),
  });
  return requestJson<CrossPaperLinksResponse>(`/graph/cross-paper-links?${params.toString()}`, { token });
}

export function getCrossPaperExploration(
  documentId: number,
  limit: number,
  minShared: number,
  query: string | undefined,
  token: string,
): Promise<CrossPaperExplorationResponse> {
  const params = new URLSearchParams({
    limit: String(limit),
    min_shared: String(minShared),
  });
  if (query && query.trim()) {
    params.set("query", query.trim());
  }
  return requestJson<CrossPaperExplorationResponse>(`/graph/cross-paper-explore/${documentId}?${params.toString()}`, { token });
}

export function getCrossPaperRecommendations(
  query: string,
  limit: number,
  seedLimit: number,
  minShared: number,
  token: string,
): Promise<CrossPaperRecommendationsResponse> {
  const params = new URLSearchParams({
    query,
    limit: String(limit),
    seed_limit: String(seedLimit),
    min_shared: String(minShared),
  });
  return requestJson<CrossPaperRecommendationsResponse>(`/graph/cross-paper-recommendations?${params.toString()}`, { token });
}

export function exportRdf(documentId: number, token: string): Promise<RdfExportResponse> {
  return requestJson<RdfExportResponse>(`/rdf/export/${documentId}`, { token });
}

export function queryChat(payload: ChatQueryRequest, token: string): Promise<ChatQueryResponse> {
  return requestJson<ChatQueryResponse>("/chat/query", {
    method: "POST",
    token,
    body: payload,
  });
}
