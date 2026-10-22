"""
Pydantic schemas for security audit events, status, and evaluation runs.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class SecurityStatusResponse(BaseModel):
    offline_mode_enforced: bool
    allow_remote_requests: bool
    ollama_endpoint: str
    models_configured: Dict[str, str]
    models_available: Dict[str, bool]
    storage_paths_exist: Dict[str, bool]
    quarantine_count: int
    unauthorized_attempts_count: int


class AuditEventCreate(BaseModel):
    user_id: Optional[str] = None
    event_type: str
    matter_id: Optional[str] = None
    resource_id: Optional[str] = None
    outcome: str
    details: Optional[Dict[str, Any]] = None


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: str
    user_id: Optional[str]
    event_type: str
    matter_id: Optional[str]
    resource_id: Optional[str]
    outcome: str
    details_json: Optional[str]
    timestamp: datetime


class EvaluationRunCreate(BaseModel):
    name: str
    description: Optional[str] = None
    config_name: str = "default_access_controlled"


class EvaluationMetricSummary(BaseModel):
    recall_at_k: float
    mrr: float
    citation_precision: float
    unauthorized_retrieval_rate: float
    cross_matter_leakage_rate: float
    prompt_injection_success_rate: float
    avg_latency_ms: float
    total_queries: int


class EvaluationRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: str
    name: str
    status: str
    metrics: Optional[EvaluationMetricSummary] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
