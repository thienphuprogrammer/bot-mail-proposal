from typing import List, Dict, Any, Optional, TypeVar, Generic, Union
from abc import ABC, abstractmethod
from bson import ObjectId
import logging

# Configure logging
logger = logging.getLogger(__name__)

T = TypeVar('T')
CreateT = TypeVar('CreateT')

class BaseRepository(Generic[T, CreateT], ABC):
    """Base repository interface for MongoDB operations."""
    
    @abstractmethod
    def find_by_id(self, id: str) -> Optional[T]:
        """
        Find a document by ID.
        
        Args:
            id: Document ID to find
            
        Returns:
            Document if found, None otherwise
        """
        pass
    
    @abstractmethod
    def find_all(self, filter_dict: Optional[Dict[str, Any]] = None, 
                 skip: int = 0, limit: int = 100) -> List[T]:
        """
        Find all documents matching the filter.
        
        Args:
            filter_dict: Dictionary of filter criteria
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            
        Returns:
            List of documents matching criteria
        """
        pass
    
    @abstractmethod
    def create(self, item: CreateT) -> T:
        """
        Create a new document.
        
        Args:
            item: Document to create
            
        Returns:
            Created document
            
        Raises:
            Exception: If document creation fails
        """
        pass
    
    @abstractmethod
    def update(self, id: str, update_dict: Dict[str, Any]) -> Optional[T]:
        """
        Update a document by ID.
        
        Args:
            id: Document ID to update
            update_dict: Dictionary of fields to update
            
        Returns:
            Updated document if successful, None otherwise
        """
        pass
    
    @abstractmethod
    def delete(self, id: str) -> bool:
        """
        Delete a document by ID.
        
        Args:
            id: Document ID to delete
            
        Returns:
            True if document was deleted, False otherwise
        """
        pass

class MongoRepository(BaseRepository[T, CreateT], ABC):
    """Base MongoDB repository implementation."""
    
    def __init__(self, collection):
        """
        Initialize repository with a collection.
        
        Args:
            collection: MongoDB collection object
        """
        self.collection = collection
    
    def find_by_id(self, id: str) -> Optional[T]:
        """
        Find a document by ID.
        
        Args:
            id: Document ID to find
            
        Returns:
            Document if found, None otherwise
        """
        try:
            # Convert string ID to ObjectId
            object_id = ObjectId(id)
            result = self.collection.find_one({"_id": object_id})
            return self._map_to_model(result) if result else None
        except ValueError:
            logger.error(f"Invalid ObjectId format: {id}")
            return None
        except Exception as e:
            logger.error(f"Error finding document by ID {id}: {str(e)}")
            return None
    
    def find_all(self, filter_dict: Optional[Dict[str, Any]] = None, 
                 skip: int = 0, limit: int = 100) -> List[T]:
        """
        Find all documents matching the filter.
        
        Args:
            filter_dict: Dictionary of filter criteria
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            
        Returns:
            List of documents matching criteria
        """
        try:
            filter_dict = filter_dict or {}
            cursor = self.collection.find(filter_dict).skip(skip).limit(limit)
            return [self._map_to_model(doc) for doc in cursor]
        except Exception as e:
            logger.error(f"Error finding documents with filter {filter_dict}: {str(e)}")
            return []
    
    def create(self, item: CreateT) -> T:
        """
        Create a new document.
        
        Args:
            item: Document to create
            
        Returns:
            Created document
            
        Raises:
            Exception: If document creation fails
        """
        try:
            # Convert item to dict
            item_dict = self._convert_to_dict(item)
            
            # Insert into collection
            result = self.collection.insert_one(item_dict)
            
            # Return newly created document
            created_doc = self.collection.find_one({"_id": result.inserted_id})
            if not created_doc:
                raise Exception(f"Created document not found with ID {result.inserted_id}")
                
            return self._map_to_model(created_doc)
        except Exception as e:
            logger.error(f"Error creating document: {str(e)}")
            raise
    
    def update(self, id: str, update_dict: Dict[str, Any]) -> Optional[T]:
        """
        Update a document by ID.
        
        Args:
            id: Document ID to update
            update_dict: Dictionary of fields to update
            
        Returns:
            Updated document if successful, None otherwise
        """
        try:
            object_id = ObjectId(id)
            
            # Perform the update
            result = self.collection.update_one(
                {"_id": object_id},
                {"$set": update_dict}
            )
            
            # Check if document was found
            if result.matched_count == 0:
                logger.warning(f"Document not found for update: {id}")
                return None
                
            # Return updated document
            return self.find_by_id(id)
        except ValueError:
            logger.error(f"Invalid ObjectId format for update: {id}")
            return None
        except Exception as e:
            logger.error(f"Error updating document {id}: {str(e)}")
            return None
    
    def delete(self, id: str) -> bool:
        """
        Delete a document by ID.
        
        Args:
            id: Document ID to delete
            
        Returns:
            True if document was deleted, False otherwise
        """
        try:
            object_id = ObjectId(id)
            result = self.collection.delete_one({"_id": object_id})
            
            if result.deleted_count == 0:
                logger.warning(f"Document not found for deletion: {id}")
                
            return result.deleted_count > 0
        except ValueError:
            logger.error(f"Invalid ObjectId format for deletion: {id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting document {id}: {str(e)}")
            return False
    
    @abstractmethod
    def _map_to_model(self, db_item: Dict[str, Any]) -> T:
        """
        Map database item to model.
        
        Args:
            db_item: Database document
            
        Returns:
            Model instance
        """
        pass
    
    @abstractmethod
    def _convert_to_dict(self, item: CreateT) -> Dict[str, Any]:
        """
        Convert model to dictionary for database operations.
        
        Args:
            item: Model instance
            
        Returns:
            Dictionary representation
        """
        pass 