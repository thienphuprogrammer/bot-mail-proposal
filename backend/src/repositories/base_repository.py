from typing import List, Dict, Any, Optional, TypeVar, Generic
from abc import ABC, abstractmethod
from bson import ObjectId

T = TypeVar('T')
CreateT = TypeVar('CreateT')

class BaseRepository(Generic[T, CreateT], ABC):
    """Base repository interface for MongoDB operations."""
    
    @abstractmethod
    def find_by_id(self, id: str) -> Optional[T]:
        """Find a document by ID."""
        pass
    
    @abstractmethod
    def find_all(self, filter_dict: Dict[str, Any] = None, 
                 skip: int = 0, limit: int = 100) -> List[T]:
        """Find all documents matching the filter."""
        pass
    
    @abstractmethod
    def create(self, item: CreateT) -> T:
        """Create a new document."""
        pass
    
    @abstractmethod
    def update(self, id: str, update_dict: Dict[str, Any]) -> Optional[T]:
        """Update a document by ID."""
        pass
    
    @abstractmethod
    def delete(self, id: str) -> bool:
        """Delete a document by ID."""
        pass

class MongoRepository(BaseRepository[T, CreateT], ABC):
    """Base MongoDB repository implementation."""
    
    def __init__(self, collection):
        """Initialize repository with a collection."""
        self.collection = collection
    
    def find_by_id(self, id: str) -> Optional[T]:
        """Find a document by ID."""
        try:
            result = self.collection.find_one({"_id": ObjectId(id)})
            return self._map_to_model(result) if result else None
        except Exception as e:
            print(f"Error finding document by ID: {e}")
            return None
    
    def find_all(self, filter_dict: Dict[str, Any] = None, 
                 skip: int = 0, limit: int = 100) -> List[T]:
        """Find all documents matching the filter."""
        try:
            filter_dict = filter_dict or {}
            cursor = self.collection.find(filter_dict).skip(skip).limit(limit)
            return [self._map_to_model(doc) for doc in cursor]
        except Exception as e:
            print(f"Error finding documents: {e}")
            return []
    
    def create(self, item: CreateT) -> T:
        """Create a new document."""
        try:
            # Convert item to dict
            item_dict = self._convert_to_dict(item)
            
            # Insert into collection
            result = self.collection.insert_one(item_dict)
            
            # Return newly created document
            created_doc = self.collection.find_one({"_id": result.inserted_id})
            return self._map_to_model(created_doc)
        except Exception as e:
            print(f"Error creating document: {e}")
            raise
    
    def update(self, id: str, update_dict: Dict[str, Any]) -> Optional[T]:
        """Update a document by ID."""
        try:
            self.collection.update_one(
                {"_id": ObjectId(id)},
                {"$set": update_dict}
            )
            return self.find_by_id(id)
        except Exception as e:
            print(f"Error updating document: {e}")
            return None
    
    def delete(self, id: str) -> bool:
        """Delete a document by ID."""
        try:
            result = self.collection.delete_one({"_id": ObjectId(id)})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False
    
    @abstractmethod
    def _map_to_model(self, db_item: Dict[str, Any]) -> T:
        """Map database item to model."""
        pass
    
    @abstractmethod
    def _convert_to_dict(self, item: CreateT) -> Dict[str, Any]:
        """Convert model to dictionary for database operations."""
        pass 