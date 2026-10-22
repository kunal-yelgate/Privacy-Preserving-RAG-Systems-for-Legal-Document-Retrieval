"""
Pydantic schemas for search requests, retrieval results, and hybrid rank fusion.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from backend.app.domain.enums import ClassificationLevel


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    matter_id: str = Field(..., min_length=1, max_length=100)
    top_k: int = Field(default=5, ge=1, le=20)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)
    classification_filter: Optional[List[ClassificationLevel]] = None


class SearchResultItem(BaseModel):
    chunk_id: str
    document_id: str
    matter_id: str
    document_title: str
    page_number: int
    text_content: str
    score: float
    semantic_score: Optional[float] = None
    keyword_score: Optional[float] = None
    classification: ClassificationLevel


class SearchResponse(BaseModel):
    query: str
    matter_id: str
    total_results: int
    results: List[SearchResultItem]
