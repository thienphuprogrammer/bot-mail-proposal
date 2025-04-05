from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List, Dict, Any, ClassVar, Literal
from datetime import datetime
from bson import ObjectId
from enum import Enum
from decimal import Decimal

from models.user import PyObjectId

class ProposalStatus(str, Enum):
    """Enum for proposal statuses."""
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SENT = "sent"

class Priority(str, Enum):
    """Enum for proposal priorities."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ApprovalDecision(str, Enum):
    """Enum for approval decisions."""
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUESTED_CHANGES = "requested_changes"

class ExtractedData(BaseModel):
    """Model for extracted data from emails."""
    project_name: str = Field(..., min_length=1, max_length=200, description="Name of the project")
    description: str = Field(..., min_length=3, description="Detailed project description")
    key_features: List[str] = Field(default_factory=list, max_items=30, description="List of key project features")
    deadline: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Project deadline")
    budget: Optional[Decimal] = Field(None, ge=0, description="Project budget")
    client_requirements: Optional[str] = Field(None, description="Specific client requirements")
    priority: Priority = Field(default=Priority.MEDIUM, description="Project priority level")
    
    @validator('deadline')
    def validate_deadline(cls, v):
        if v and v < datetime.utcnow():
            # Add debugging to understand the comparison
            current_time = datetime.utcnow()
            print(f"Deadline validation: {v} < {current_time} = {v < current_time}")
            # If dates are the same or deadline is in future, allow it
            # This handles timezone issues by comparing only dates when they're close
            if v.date() >= current_time.date() or (current_time - v).total_seconds() < 86400:  # Within 24 hours
                return v
            raise ValueError('Deadline cannot be in the past')
        return v
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class ProposalVersion(BaseModel):
    """Model for a proposal version."""
    content: str = Field(..., min_length=1, description="HTML content of the proposal")
    pdf_path: Optional[str] = Field(None, description="Path to the PDF version")
    version: int = Field(..., ge=1, description="Version number")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    modified_by: Optional[PyObjectId] = Field(None, description="User who modified this version")
    
    @validator('version')
    def validate_version(cls, v):
        if v < 1:
            raise ValueError('Version number must be greater than 0')
        return v
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class ApprovalHistory(BaseModel):
    """Model for approval history."""
    user_id: PyObjectId = Field(..., description="User who made the decision")
    decision: ApprovalDecision = Field(..., description="Approval decision")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Decision timestamp")
    comments: Optional[str] = Field(None, max_length=1000, description="Comments on the decision")
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class ProposalBase(BaseModel):
    """Base model for Proposal."""
    email_id: PyObjectId = Field(..., description="Reference to the source email")
    extracted_data: ExtractedData = Field(..., description="Extracted data from email")
    proposal_versions: List[ProposalVersion] = Field(default_factory=list, description="List of proposal versions")
    current_status: ProposalStatus = Field(default=ProposalStatus.DRAFT, description="Current proposal status")
    approval_history: List[ApprovalHistory] = Field(default_factory=list, description="History of approval decisions")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('proposal_versions')
    def validate_versions(cls, v):
        if not v:
            return v
            
        # Check if versions are sequential
        versions = [ver.version for ver in v]
        if versions != list(range(1, len(versions) + 1)):
            raise ValueError('Version numbers must be sequential starting from 1')
            
        # Check if versions are sorted by version number
        if not all(v[i].version <= v[i+1].version for i in range(len(v)-1)):
            raise ValueError('Versions must be sorted by version number')
            
        return v
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class ProposalCreate(ProposalBase):
    """Model for creating a new proposal."""
    pass

class Proposal(ProposalBase):
    """Model for a proposal returned from API."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id", description="Proposal ID")
    timestamps: Dict[str, datetime] = Field(
        default_factory=lambda: {
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "sent_at": None
        },
        description="Timestamps for various events"
    )
    
    @validator('timestamps')
    def validate_timestamps(cls, v):
        if v.get('sent_at') and v['sent_at'] < v.get('created_at'):
            raise ValueError('Sent timestamp cannot be before creation timestamp')
        return v
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class ProposalUpdate(BaseModel):
    """Model for updating a proposal."""
    extracted_data: Optional[ExtractedData] = None
    proposal_versions: Optional[List[ProposalVersion]] = None
    current_status: Optional[ProposalStatus] = None
    approval_history: Optional[List[ApprovalHistory]] = None
    timestamps: Optional[Dict[str, datetime]] = None
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class ProposalApproval(BaseModel):
    """Model for approving a proposal."""
    user_id: PyObjectId = Field(..., description="User making the approval decision")
    decision: ApprovalDecision = Field(..., description="Approval decision")
    comments: Optional[str] = Field(None, max_length=1000, description="Comments on the decision")
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    ) 