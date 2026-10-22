"""
Pydantic schemas for document ingestion, metadata, and responses.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from backend.app.domain.enums import ClassificationLevel, IngestionStatus


class DocumentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    matter_id: str = Field(..., min_length=1, max_length=100)
    classification: ClassificationLevel = ClassificationLevel.CONFIDENTIAL
    description: Optional[str] = None


class DocumentCreate(DocumentBase):
    pass


class DocumentMetadata(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: str
    matter_id: str
    title: str
    original_filename: str
    file_extension: str
    file_size_bytes: int
    content_hash: str
    classification: ClassificationLevel
    status: IngestionStatus
    total_pages: int = 0
    total_chunks: int = 0
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DocumentChunkSchema(BaseModel):
    chunk_id: str
    document_id: str
    matter_id: str
    chunk_index: int
    page_number: int
    text_content: str
    token_count: Optional[int] = None
    classification: ClassificationLevel
    created_at: datetime
