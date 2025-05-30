from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from typing import Dict, Any, Optional
import logging

from src.core.config import settings

logger = logging.getLogger(__name__)

class MongoDB:
    """MongoDB connection and operations handler."""
    
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None
    
    @classmethod
    def connect(cls) -> None:
        """Connect to MongoDB database."""
        if cls._client is None:
            cls._client = MongoClient(settings.MONGODB_URI)
            cls._db = cls._client[settings.MONGODB_DB_NAME]
            logger.info(f"Connected to MongoDB: {settings.MONGODB_DB_NAME}")
    
    @classmethod
    def disconnect(cls) -> None:
        """Close MongoDB connection."""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None
            logger.info("Disconnected from MongoDB")
    
    @classmethod
    def get_collection(cls, collection_name: str) -> Collection:
        """Get a MongoDB collection."""
        if cls._db is None:
            cls.connect()
        return cls._db[collection_name]
    
    @classmethod
    def create_indexes(cls) -> None:
        """Create indexes for collections."""
        # Users collection indexes
        users_collection = cls.get_collection("users")
        users_collection.create_index("email", unique=True)
        
        # Emails collection indexes
        emails_collection = cls.get_collection("emails")
        emails_collection.create_index("email_id", unique=True)
        emails_collection.create_index("is_processed")
        
        # Proposals collection indexes
        proposals_collection = cls.get_collection("proposals")
        proposals_collection.create_index("email_id")
        proposals_collection.create_index("status")
        
        logger.info("Created MongoDB indexes")

# Initialize database connection
def init_db():
    """Initialize database connection and setup."""
    try:
        MongoDB.connect()
        MongoDB.create_indexes()
        logger.info("Database initialized successfully")
        return MongoDB
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        raise

# Get a MongoDB instance
def get_db() -> MongoDB:
    """Get MongoDB instance."""
    if MongoDB._client is None:
        MongoDB.connect()
    return MongoDB 