from typing import Dict, Any, List, Optional
from datetime import datetime
from bson import ObjectId

from src.repositories.base_repository import MongoRepository
from src.models.email import Email, EmailCreate, EmailUpdate
from src.database.mongodb import MongoDB
from src.core.config import settings
from src.utils.crypto import encrypt_data, decrypt_data

class EmailRepository(MongoRepository[Email, EmailCreate]):
    """Repository for Email operations."""
    
    def __init__(self):
        """Initialize repository with email collection."""
        super().__init__(MongoDB.get_collection("emails"))
        # Get encryption key from settings
        self.encryption_key = settings.ENCRYPTION_KEY.encode() if hasattr(settings, 'ENCRYPTION_KEY') else None
    
    def _map_to_model(self, db_item: Dict[str, Any]) -> Email:
        """Map database item to Email model."""
        if not db_item:
            return None
            
        # Convert _id to string
        db_item["id"] = str(db_item.pop("_id"))
        
        # Decrypt sensitive fields if needed
        if "body" in db_item and db_item.get("is_encrypted", False):
            try:
                encrypted_body = db_item["body"]
                if isinstance(encrypted_body, str):
                    encrypted_body = encrypted_body.encode()
                # Use decrypt_data with default key handling
                db_item["body"] = decrypt_data(encrypted_body)
                db_item["is_encrypted"] = False
            except Exception as e:
                print(f"Error decrypting email body: {e}")
        
        # Create Email object
        return Email(**db_item)
    
    def _convert_to_dict(self, item: EmailCreate) -> Dict[str, Any]:
        """Convert EmailCreate to dictionary for database operations."""
        email_dict = item.model_dump(by_alias=True, exclude_unset=True)
        
        # Encrypt sensitive fields using settings.ENCRYPTION_KEY
        if "body" in email_dict and email_dict["body"]:
            try:
                # Let encrypt_data use default key handling
                encrypted_body, _ = encrypt_data(email_dict["body"])
                email_dict["body"] = encrypted_body
                email_dict["is_encrypted"] = True
            except Exception as e:
                print(f"Error encrypting email body: {e}")
        
        return email_dict
    
    def find_by_mail_id(self, mail_id: str) -> Optional[Email]:
        """Find email by Mail ID."""
        result = self.collection.find_one({"mail_id": mail_id})
        return self._map_to_model(result) if result else None
    
    def find_unprocessed(self, limit: int = 10) -> List[Email]:
        """Find unprocessed emails."""
        cursor = self.collection.find({"processing_status": "pending"}).limit(limit)
        return [self._map_to_model(doc) for doc in cursor]
    
    def update_status(self, email_id: str, status: str, error_log: str = None) -> Optional[Email]:
        """Update email processing status."""
        update_dict = {"processing_status": status}
        if error_log:
            update_dict["error_log"] = error_log
        
        return self.update(email_id, update_dict) 