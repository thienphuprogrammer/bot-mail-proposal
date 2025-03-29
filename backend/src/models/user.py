from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from bson import ObjectId

class PyObjectId(str):
    """Custom ObjectId class for Pydantic."""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
        
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class UserBase(BaseModel):
    """Base model for User."""
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "editor"  # Default to 'editor' role
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

class UserCreate(UserBase):
    """Model for creating a new user."""
    password: str
    
class UserInDB(UserBase):
    """Model for a user in the database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

class User(UserBase):
    """Model for a user returned from API."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

class UserUpdate(BaseModel):
    """Model for updating a user."""
    full_name: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        } 