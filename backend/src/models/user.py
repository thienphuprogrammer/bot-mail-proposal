from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Any, ClassVar
from datetime import datetime
from bson import ObjectId
from pydantic_core import core_schema

class PyObjectId(str):
    """Custom ObjectId class for Pydantic."""
    
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> core_schema.CoreSchema:
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ]),
        ])
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __get_pydantic_json_schema__(cls, _schema, _handler):
        return {"type": "string"}

class UserBase(BaseModel):
    """Base model for User."""
    email: EmailStr
    full_name: str
    role: str = "staff"  # staff, admin, client
    
    model_config: ClassVar[dict] = {
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ObjectId: str
        }
    }

class UserCreate(UserBase):
    """Model for creating a new user."""
    password: str
    
class UserInDB(UserBase):
    """Model for a user in the database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    model_config: ClassVar[dict] = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ObjectId: str
        }
    }

class User(UserBase):
    """Model for a user returned from src.api."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime
    last_login: Optional[datetime] = None
    password_hash: Optional[str] = None
    
    model_config: ClassVar[dict] = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ObjectId: str
        }
    }

class UserUpdate(BaseModel):
    """Model for updating a user."""
    full_name: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None
    last_login: Optional[datetime] = None
    
    model_config: ClassVar[dict] = {
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ObjectId: str
        }
    } 