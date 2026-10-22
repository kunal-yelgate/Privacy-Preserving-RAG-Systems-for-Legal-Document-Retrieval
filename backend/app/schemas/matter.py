"""
Pydantic schemas for legal matters and access control memberships.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from backend.app.domain.enums import MatterStatus, UserRole


class MatterBase(BaseModel):
    matter_id: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-zA-Z0-9_\-]+$")
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    client_name: Optional[str] = None
    lead_counsel: Optional[str] = None


class MatterCreate(MatterBase):
    pass


class MatterUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    client_name: Optional[str] = None
    lead_counsel: Optional[str] = None
    status: Optional[MatterStatus] = None


class MatterResponse(MatterBase):
    model_config = ConfigDict(from_attributes=True)

    status: MatterStatus = MatterStatus.ACTIVE
    created_at: datetime
    updated_at: datetime
    document_count: int = 0


class MatterMembershipCreate(BaseModel):
    user_id: str
    role: UserRole = UserRole.RESEARCHER


class MatterMembershipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    matter_id: str
    role: UserRole
    granted_at: datetime
