from typing import Dict, Any, List, Optional
from bson import ObjectId

from src.database.mongodb import MongoDB
from src.repositories.base_repository import MongoRepository

class TemplateRepository(MongoRepository):
    """Repository for template operations."""

    def __init__(self):
        """Initialize repository with templates collection."""
        super().__init__(MongoDB.get_collection("templates"))
    
    def _map_to_model(self, db_item: Dict[str, Any]) -> Dict[str, Any]:
        """Map database item to template dictionary."""
        if not db_item:
            return None
        return db_item
    
    def _convert_to_dict(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert template dictionary for database operations."""
        return item
    
    def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find template by name."""
        result = self.collection.find_one({"name": name})
        return self._map_to_model(result) if result else None
    
    def find_by_creator(self, user_id: str) -> List[Dict[str, Any]]:
        """Find templates created by a user."""
        cursor = self.collection.find({"created_by": ObjectId(user_id)})
        return [self._map_to_model(doc) for doc in cursor] 