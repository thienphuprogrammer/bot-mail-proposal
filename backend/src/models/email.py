from pydantic import BaseModel, Field
from typing import Optional, List, ClassVar
from datetime import datetime
from bson import ObjectId

from src.models.user import PyObjectId

class EmailBase(BaseModel):
    """Base model for Email."""
    email_id: str
    sender: str
    subject: str
    body: str
    attachments: List[str] = []
    received_at: datetime = Field(default_factory=datetime.utcnow)
    processing_status: str = "pending"  # pending, processing, completed, failed
    error_log: Optional[str] = None
    is_encrypted: bool = False
    
    model_config: ClassVar[dict] = {
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ObjectId: str
        }
    }

class EmailCreate(EmailBase):
    """Model for creating a new email."""
    pass

class Email(EmailBase):
    """Model for an email returned from src.api."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    @property
    def processed(self) -> bool:
        """Returns True if the email has been processed successfully."""
        return self.processing_status == "completed"
    
    model_config: ClassVar[dict] = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ObjectId: str
        }
    }

class EmailUpdate(BaseModel):
    """Model for updating an email."""
    processing_status: Optional[str] = None
    error_log: Optional[str] = None
    
    model_config: ClassVar[dict] = {
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ObjectId: str
        }
    }

class SentEmailBase(BaseModel):
    """Base model for a sent email."""
    proposal_id: PyObjectId
    recipients: List[str]
    subject: str
    content: str
    attachments: List[dict] = []
    gmail_data: dict = {"message_id": "", "thread_id": ""}
    outlook_data: dict = {"message_id": "", "thread_id": ""}
    delivery_status: dict = {"status": "queued", "error": None, "retries": 0}
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    opened_at: Optional[datetime] = None
    is_encrypted: bool = False
    
    model_config: ClassVar[dict] = {
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ObjectId: str
        }
    }

class SentEmailCreate(SentEmailBase):
    """Model for creating a new sent email."""
    pass

class SentEmail(SentEmailBase):
    """Model for a sent email returned from src.api."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    model_config: ClassVar[dict] = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ObjectId: str
        }
    } 