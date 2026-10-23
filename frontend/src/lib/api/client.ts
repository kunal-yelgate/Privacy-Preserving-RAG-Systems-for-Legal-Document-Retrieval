/**
 * Typed API Client for Privacy-Preserving Offline Legal RAG.
 * Connects exclusively to local backend loopback endpoint (127.0.0.1:8000).
 */
import {
  AuditEvent,
  AuthToken,
  ChatResponse,
  ChatMessage,
  ChatSession,
  CitationReference,
  ClassificationLevel,
  DocumentMetadata,
  EvaluationRun,
  Matter,
  SearchResultItem,
  SecurityStatus,
  User,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

export class ApiError extends Error {
  status?: number;
  isConnectionError: boolean;
  endpoint: string;
  details?: any;

  constructor(
    message: string,
    options: {
      status?: number;
      isConnectionError?: boolean;
      endpoint: string;
      details?: any;
    }
  ) {
    super(message);
    this.name = "ApiError";
    this.status = options.status;
    this.isConnectionError = !!options.isConnectionError;
    this.endpoint = options.endpoint;
    this.details = options.details;
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

export function isApiError(err: unknown): err is ApiError {
  return err instanceof ApiError;
}

export function getErrorMessage(err: unknown, fallback = "An unexpected error occurred."): string {
  if (err instanceof ApiError) {
    return err.message;
  }
  if (err instanceof Error) {
    if (err.name === "TypeError" && err.message.toLowerCase().includes("fetch")) {
      return `Failed to connect to backend at ${API_BASE}. Ensure the FastAPI server is running on 127.0.0.1:8000.`;
    }
    return err.message;
  }
  return fallback;
}

class ApiClient {
  private token: string | null = null;

  constructor() {
    if (typeof window !== "undefined") {
      this.token = sessionStorage.getItem("legal_rag_token");
    }
  }

  setToken(token: string | null) {
    this.token = token;
    if (typeof window !== "undefined") {
      if (token) {
        sessionStorage.setItem("legal_rag_token", token);
      } else {
        sessionStorage.removeItem("legal_rag_token");
      }
    }
  }

  getToken(): string | null {
    if (!this.token && typeof window !== "undefined") {
      this.token = sessionStorage.getItem("legal_rag_token");
    }
    return this.token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const headers = new Headers(options.headers || {});

    const token = this.getToken();
    if (token && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }

    let response: Response;
    try {
      response = await fetch(url, {
        ...options,
        headers,
      });
    } catch (networkErr: any) {
      const details = networkErr?.message || "Failed to fetch";
      throw new ApiError(
        `Unable to reach local backend at ${API_BASE}. Please verify that the FastAPI backend is running on 127.0.0.1:8000. (${details})`,
        {
          isConnectionError: true,
          endpoint,
          details,
        }
      );
    }

    if (response.status === 204) {
      return {} as T;
    }

    let data: any = null;
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      try {
        data = await response.json();
      } catch (parseErr) {
        data = { message: `Received invalid JSON from ${endpoint} (Status ${response.status})` };
      }
    } else {
      try {
        const text = await response.text();
        data = { message: text || `HTTP ${response.status} from ${endpoint}` };
      } catch {
        data = { message: `HTTP ${response.status} from ${endpoint}` };
      }
    }

    if (!response.ok) {
      if (response.status === 401) {
        this.setToken(null);
      }
      const errorMsg =
        data?.detail ||
        data?.message ||
        `Request to ${endpoint} failed with HTTP status ${response.status}`;
      throw new ApiError(errorMsg, {
        status: response.status,
        endpoint,
        details: data,
      });
    }

    return data as T;
  }

  // --- Auth Endpoints ---
  async login(username: string, password: string): Promise<AuthToken> {
    const res = await this.request<AuthToken>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    this.setToken(res.access_token);
    return res;
  }

  async getMe(): Promise<User> {
    return this.request<User>("/auth/me");
  }

  logout() {
    this.setToken(null);
  }

  // --- Health & Readiness ---
  async getHealth(): Promise<{ status: string; offline_mode: boolean }> {
    return this.request<{ status: string; offline_mode: boolean }>("/health");
  }

  async getReadiness(): Promise<{
    ready: boolean;
    subsystems: Record<string, boolean>;
    offline_mode: boolean;
  }> {
    return this.request<{
      ready: boolean;
      subsystems: Record<string, boolean>;
      offline_mode: boolean;
    }>("/health/ready");
  }

  // --- Matters ---
  async listMatters(): Promise<Matter[]> {
    return this.request<Matter[]>("/matters");
  }

  async createMatter(data: {
    matter_id: string;
    name: string;
    description?: string;
    client_name?: string;
    lead_counsel?: string;
  }): Promise<Matter> {
    return this.request<Matter>("/matters", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getMatter(matterId: string): Promise<Matter> {
    return this.request<Matter>(`/matters/${matterId}`);
  }

  async deleteMatter(matterId: string): Promise<void> {
    return this.request<void>(`/matters/${matterId}`, {
      method: "DELETE",
    });
  }

  // --- Documents ---
  async listDocuments(matterId: string): Promise<DocumentMetadata[]> {
    return this.request<DocumentMetadata[]>(`/documents?matter_id=${encodeURIComponent(matterId)}`);
  }

  async uploadDocument(
    file: File,
    matterId: string,
    title?: string,
    classification: ClassificationLevel = "confidential"
  ): Promise<DocumentMetadata> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("matter_id", matterId);
    if (title) formData.append("title", title);
    formData.append("classification", classification);

    return this.request<DocumentMetadata>("/documents", {
      method: "POST",
      body: formData,
    });
  }

  async deleteDocument(documentId: string): Promise<void> {
    return this.request<void>(`/documents/${documentId}`, {
      method: "DELETE",
    });
  }

  // --- Search ---
  async search(
    query: string,
    matterId: string,
    topK = 5
  ): Promise<{ query: string; matter_id: string; total_results: number; results: SearchResultItem[] }> {
    return this.request<{ query: string; matter_id: string; total_results: number; results: SearchResultItem[] }>("/search", {
      method: "POST",
      body: JSON.stringify({ query, matter_id: matterId, top_k: topK }),
    });
  }

  // --- Chat / Research ---
  async askQuestion(
    question: string,
    matterId: string,
    sessionId?: string,
    topK = 4
  ): Promise<ChatResponse> {
    return this.request<ChatResponse>("/chat", {
      method: "POST",
      body: JSON.stringify({ question, matter_id: matterId, session_id: sessionId, top_k: topK }),
    });
  }

  async listChatSessions(matterId?: string): Promise<ChatSession[]> {
    const q = matterId ? `?matter_id=${encodeURIComponent(matterId)}` : "";
    return this.request<ChatSession[]>(`/chat/sessions${q}`);
  }

  async getSessionMessages(sessionId: string): Promise<ChatMessage[]> {
    return this.request<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`);
  }

  // --- Citations ---
  async getCitation(chunkId: string): Promise<CitationReference> {
    return this.request<CitationReference>(`/citations/${chunkId}`);
  }

  // --- Security ---
  async getSecurityStatus(): Promise<SecurityStatus> {
    return this.request<SecurityStatus>("/security/status");
  }

  async listAuditEvents(limit = 30): Promise<AuditEvent[]> {
    return this.request<AuditEvent[]>(`/security/audit?limit=${limit}`);
  }

  // --- Evaluation ---
  async runEvaluation(): Promise<EvaluationRun> {
    return this.request<EvaluationRun>("/evaluation/runs", {
      method: "POST",
    });
  }

  async listEvaluationRuns(): Promise<EvaluationRun[]> {
    return this.request<EvaluationRun[]>("/evaluation/runs");
  }
}

export const api = new ApiClient();
