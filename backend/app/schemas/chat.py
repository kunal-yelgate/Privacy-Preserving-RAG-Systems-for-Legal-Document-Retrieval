"""
Pydantic schemas for LLM generation, chat sessions, evidence citations, and evaluation.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CitationReference(BaseModel):
    citation_id: str
    chunk_id: str
    document_id: str
    document_title: str
    matter_id: str
    page_number: int
    snippet: str


class ChatRequest(BaseModel):
    matter_id: str = Field(..., min_length=1, max_length=100)
    question: str = Field(..., min_length=3, max_length=1000)
    session_id: Optional[str] = None
    top_k: int = Field(default=4, ge=1, le=10)


class ChatResponse(BaseModel):
    answer: str
    matter_id: str
    session_id: str
    evidence_found: bool
    citations: List[CitationReference]
    generated_at: datetime
    model_name: str
    disclaimer: str = (
        "This answer is generated offline using retrieved documentary evidence. "
        "It does not constitute formal legal advice or replace professional counsel."
    )


class ChatMessageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message_id: str
    session_id: str
    sender: str
    content: str
    citations_json: Optional[str] = None
    created_at: datetime


class ChatSessionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    matter_id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
