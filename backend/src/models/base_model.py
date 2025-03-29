from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel as PydanticBaseModel, Field

class BaseModel(PydanticBaseModel):
    """Base model for all models in the application."""
    
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        """Pydantic configuration."""
        
        orm_mode = True
        allow_population_by_field_name = True
        
        # Add schema_extra for OpenAPI documentation
        schema_extra = {
            "example": {
                "id": "5f8d0f1e7b6e1d1f1c9b4567",
                "created_at": "2023-03-29T12:00:00",
                "updated_at": "2023-03-29T12:00:00"
            }
        }

class CreateBaseModel(PydanticBaseModel):
    """Base model for create operations."""
    
    class Config:
        """Pydantic configuration."""
        
        orm_mode = True
        allow_population_by_field_name = True
        
class UpdateBaseModel(PydanticBaseModel):
    """Base model for update operations."""
    
    class Config:
        """Pydantic configuration."""
        
        orm_mode = True
        allow_population_by_field_name = True
        extra = "ignore"  # Ignore extra fields 