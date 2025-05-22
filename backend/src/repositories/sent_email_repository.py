from typing import Dict, Any, List, Optional
from datetime import datetime
from bson import ObjectId

from src.database.mongodb import MongoDB
from src.models.email import SentEmail, SentEmailCreate
from src.repositories.base_repository import MongoRepository
from src.core.config import settings
from src.utils.crypto import encrypt_data, decrypt_data

class SentEmailRepository(MongoRepository[SentEmail, SentEmailCreate]):
    """Repository for SentEmail operations."""

    def __init__(self):
        """Initialize repository with sent_emails collection."""
        super().__init__(MongoDB.get_collection("sent_emails"))
        # Get encryption key from settings
        self.encryption_key = settings.ENCRYPTION_KEY.encode() if hasattr(settings, 'ENCRYPTION_KEY') else None
    
    def _map_to_model(self, db_item: Dict[str, Any]) -> SentEmail:
        """Map database item to SentEmail model."""
        if not db_item:
            return None
            
        # Convert _id to string
        db_item["id"] = str(db_item.pop("_id"))
        
        # Convert proposal_id to string if it's an ObjectId
        if isinstance(db_item.get("proposal_id"), ObjectId):
            db_item["proposal_id"] = str(db_item["proposal_id"])
            
        # Decrypt sensitive content if needed
        if "content" in db_item and db_item.get("is_encrypted", False):
            try:
                encrypted_content = db_item["content"]
                if isinstance(encrypted_content, str):
                    encrypted_content = encrypted_content.encode()
                # Use decrypt_data with default key handling
                db_item["content"] = decrypt_data(encrypted_content)
                db_item["is_encrypted"] = False
            except Exception as e:
                print(f"Error decrypting email content: {e}")
        
        # Create SentEmail object
        return SentEmail(**db_item)
    
    def _convert_to_dict(self, item: SentEmailCreate) -> Dict[str, Any]:
        """Convert SentEmailCreate to dictionary for database operations."""
        email_dict = item.model_dump(by_alias=True, exclude_unset=True)
        
        # Encrypt sensitive content using settings.ENCRYPTION_KEY
        if "content" in email_dict and email_dict["content"]:
            try:
                # Let encrypt_data use default key handling
                encrypted_content, _ = encrypt_data(email_dict["content"])
                email_dict["content"] = encrypted_content
                email_dict["is_encrypted"] = True
            except Exception as e:
                print(f"Error encrypting email content: {e}")
        
        return email_dict
    
    def find_by_proposal_id(self, proposal_id: str) -> List[SentEmail]:
        """Find sent emails by proposal ID."""
        cursor = self.collection.find({"proposal_id": ObjectId(proposal_id)})
        return [self._map_to_model(doc) for doc in cursor]
    
    def update_gmail_data(self, email_id: str, message_id: str, thread_id: str) -> Optional[SentEmail]:
        """Update Gmail data for a sent email."""
        update_dict = {
            "gmail_data.message_id": message_id,
            "gmail_data.thread_id": thread_id
        }
        return self.update(email_id, update_dict)
    
    def update_delivery_status(self, email_id: str, status: str, error: str = None) -> Optional[SentEmail]:
        """Update delivery status for a sent email."""
        update_dict = {"delivery_status.status": status}
        if error:
            update_dict["delivery_status.error"] = error
        return self.update(email_id, update_dict)
    
    def track_open(self, email_id: str) -> Optional[SentEmail]:
        """Track when email was opened."""
        update_dict = {"opened_at": datetime.utcnow()}
        return self.update(email_id, update_dict)