from typing import Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from src.repositories.base_repository import MongoRepository
from src.models.email import SentEmail, SentEmailCreate
from src.database.mongodb import MongoDB

class SentEmailRepository(MongoRepository[SentEmail, SentEmailCreate]):
    """Repository for sent email operations."""
    
    def __init__(self):
        """Initialize the sent email repository."""
        super().__init__(MongoDB.get_collection("sent_emails"))
    
    def _map_to_model(self, db_item: Dict[str, Any]) -> Optional[SentEmail]:
        """Map database item to SentEmail model."""
        if not db_item:
            return None
            
        # Convert _id to string
        db_item["id"] = str(db_item.pop("_id"))
        
        # Convert ObjectId fields to strings
        if "proposal_id" in db_item and isinstance(db_item["proposal_id"], ObjectId):
            db_item["proposal_id"] = str(db_item["proposal_id"])
        
        # Create SentEmail object
        return SentEmail(**db_item)
    
    def _convert_to_dict(self, item: SentEmailCreate) -> Dict[str, Any]:
        """Convert SentEmailCreate to dictionary for database operations."""
        # Convert model to dict
        item_dict = item.dict(exclude_none=True)
        
        # Add created_at if not present
        if "created_at" not in item_dict:
            item_dict["created_at"] = datetime.utcnow()
            
        # Convert string IDs to ObjectId if needed
        if "proposal_id" in item_dict and isinstance(item_dict["proposal_id"], str):
            item_dict["proposal_id"] = ObjectId(item_dict["proposal_id"])
            
        return item_dict 