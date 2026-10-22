export type UserRole = "admin" | "researcher" | "viewer";
export type ClassificationLevel = "public" | "internal" | "confidential" | "highly_confidential";
export type IngestionStatus = "pending" | "parsing" | "chunking" | "indexing" | "completed" | "failed" | "quarantined";
export type MatterStatus = "active" | "archived" | "closed";

export interface User {
  user_id: string;
  username: string;
  role: UserRole;
  full_name?: string;
  created_at: string;
  is_active: boolean;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  user_id: string;
  username: string;
  role: UserRole;
}

export interface Matter {
  matter_id: string;
  name: string;
  description?: string;
  client_name?: string;
  lead_counsel?: string;
  status: MatterStatus;
  created_at: string;
  updated_at: string;
  document_count: number;
}

export interface DocumentMetadata {
  document_id: string;
  matter_id: string;
  title: string;
  original_filename: string;
  file_extension: string;
  file_size_bytes: number;
  content_hash: string;
  classification: ClassificationLevel;
  status: IngestionStatus;
  total_pages: number;
  total_chunks: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface SearchResultItem {
  chunk_id: string;
  document_id: string;
  matter_id: string;
  document_title: string;
  page_number: number;
  text_content: string;
  score: number;
  semantic_score?: number;
  keyword_score?: number;
  classification: ClassificationLevel;
}

export interface CitationReference {
  citation_id: string;
  chunk_id: string;
  document_id: string;
  document_title: string;
  matter_id: string;
  page_number: number;
  snippet: string;
}

export interface ChatResponse {
  answer: string;
  matter_id: string;
  session_id: string;
  evidence_found: boolean;
  citations: CitationReference[];
  generated_at: string;
  model_name: string;
  disclaimer: string;
}

export interface ChatSession {
  session_id: string;
  matter_id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  message_id: string;
  session_id: string;
  sender: string;
  content: string;
  citations_json?: string;
  created_at: string;
}

export interface SecurityStatus {
  offline_mode_enforced: boolean;
  allow_remote_requests: boolean;
  ollama_endpoint: string;
  models_configured: {
    embedding: string;
    generation: string;
  };
  models_available: Record<string, boolean>;
  storage_paths_exist: Record<string, boolean>;
  quarantine_count: number;
  unauthorized_attempts_count: number;
}

export interface AuditEvent {
  event_id: string;
  user_id?: string;
  event_type: string;
  matter_id?: string;
  resource_id?: string;
  outcome: string;
  details_json?: string;
  timestamp: string;
}

export interface EvaluationMetricSummary {
  recall_at_k: number;
  mrr: number;
  citation_precision: number;
  unauthorized_retrieval_rate: number;
  cross_matter_leakage_rate: number;
  prompt_injection_success_rate: number;
  avg_latency_ms: number;
  total_queries: number;
}

export interface EvaluationRun {
  run_id: string;
  name: string;
  status: string;
  metrics?: EvaluationMetricSummary;
  created_at: string;
  completed_at?: string;
}
