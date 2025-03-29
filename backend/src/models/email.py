from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

from src.models.user import PyObjectId

class EmailBase(BaseModel):
    """Base model for Email."""
    gmail_id: str
    sender: str
    subject: str
    body: str
    received_at: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = False
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

class EmailCreate(EmailBase):
    """Model for creating a new email."""
    pass

class Email(EmailBase):
    """Model for an email returned from API."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

class EmailUpdate(BaseModel):
    """Model for updating an email."""
    processed: Optional[bool] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

class SentEmailBase(BaseModel):
    """Base model for a sent email."""
    proposal_id: PyObjectId
    recipient: str
    subject: str
    body: str
    attachment: Optional[str] = None
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    gmail_message_id: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

class SentEmailCreate(SentEmailBase):
    """Model for creating a new sent email."""
    pass

class SentEmail(SentEmailBase):
    """Model for a sent email returned from API."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        } 