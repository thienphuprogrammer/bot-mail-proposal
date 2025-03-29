from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId

from src.models.user import PyObjectId

class ExtractedData(BaseModel):
    """Model for extracted data from emails."""
    project_name: str
    description: str
    features: List[str]
    deadline: str
    budget: Optional[float] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

class ProposalBase(BaseModel):
    """Base model for Proposal."""
    email_id: PyObjectId
    extracted_data: ExtractedData
    proposal_html: str
    status: str = "pending"  # pending, approved, sent
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

class ProposalCreate(ProposalBase):
    """Model for creating a new proposal."""
    pass

class Proposal(ProposalBase):
    """Model for a proposal returned from API."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    approved_by: Optional[PyObjectId] = None
    sent_email_id: Optional[PyObjectId] = None
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

class ProposalUpdate(BaseModel):
    """Model for updating a proposal."""
    extracted_data: Optional[ExtractedData] = None
    proposal_html: Optional[str] = None
    status: Optional[str] = None
    approved_by: Optional[PyObjectId] = None
    sent_email_id: Optional[PyObjectId] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

class ProposalApproval(BaseModel):
    """Model for approving a proposal."""
    approved_by: PyObjectId
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        } 