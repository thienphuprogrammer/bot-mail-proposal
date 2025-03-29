from typing import Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from src.repositories.base_repository import MongoRepository
from src.models.email import Email, EmailCreate
from src.database.mongodb import MongoDB

class EmailRepository(MongoRepository[Email, EmailCreate]):
    """Repository for email operations."""
    
    def __init__(self):
        """Initialize the email repository."""
        super().__init__(MongoDB.get_collection("emails"))
    
    def _map_to_model(self, db_item: Dict[str, Any]) -> Optional[Email]:
        """Map database item to Email model."""
        if not db_item:
            return None
            
        # Convert _id to string
        db_item["id"] = str(db_item.pop("_id"))
        
        # Create Email object
        return Email(**db_item)
    
    def _convert_to_dict(self, item: EmailCreate) -> Dict[str, Any]:
        """Convert EmailCreate to dictionary for database operations."""
        # Convert model to dict
        item_dict = item.dict(exclude_none=True)
        
        # Add created_at if not present
        if "created_at" not in item_dict:
            item_dict["created_at"] = datetime.utcnow()
            
        return item_dict 