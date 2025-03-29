from typing import Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from src.repositories.base_repository import MongoRepository
from src.models.proposal import Proposal, ProposalCreate
from src.database.mongodb import MongoDB

class ProposalRepository(MongoRepository[Proposal, ProposalCreate]):
    """Repository for proposal operations."""
    
    def __init__(self):
        """Initialize the proposal repository."""
        super().__init__(MongoDB.get_collection("proposals"))
    
    def _map_to_model(self, db_item: Dict[str, Any]) -> Optional[Proposal]:
        """Map database item to Proposal model."""
        if not db_item:
            return None
            
        # Convert _id to string
        db_item["id"] = str(db_item.pop("_id"))
        
        # Convert ObjectId fields to strings
        if "email_id" in db_item and isinstance(db_item["email_id"], ObjectId):
            db_item["email_id"] = str(db_item["email_id"])
            
        if "sent_email_id" in db_item and isinstance(db_item["sent_email_id"], ObjectId):
            db_item["sent_email_id"] = str(db_item["sent_email_id"])
            
        if "approved_by" in db_item and isinstance(db_item["approved_by"], ObjectId):
            db_item["approved_by"] = str(db_item["approved_by"])
        
        # Create Proposal object
        return Proposal(**db_item)
    
    def _convert_to_dict(self, item: ProposalCreate) -> Dict[str, Any]:
        """Convert ProposalCreate to dictionary for database operations."""
        # Convert model to dict
        item_dict = item.dict(exclude_none=True)
        
        # Add created_at if not present
        if "created_at" not in item_dict:
            item_dict["created_at"] = datetime.utcnow()
            
        # Convert string IDs to ObjectId if needed
        if "email_id" in item_dict and isinstance(item_dict["email_id"], str):
            item_dict["email_id"] = ObjectId(item_dict["email_id"])
            
        # Extract extracted_data to avoid nested document issues
        if "extracted_data" in item_dict and item_dict["extracted_data"]:
            extracted_data = item_dict["extracted_data"]
            if hasattr(extracted_data, "dict"):
                item_dict["extracted_data"] = extracted_data.dict()
            
        return item_dict 