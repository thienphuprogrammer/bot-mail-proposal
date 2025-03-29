from typing import Dict, Any, Optional, List
from datetime import datetime
from bson import ObjectId
from passlib.context import CryptContext

from src.models.user import User, UserCreate, UserUpdate
from src.repositories.base_repository import MongoRepository
from src.database.mongodb import MongoDB

class UserRepository(MongoRepository[User, UserCreate]):
    """Repository for user operations."""
    
    def __init__(self):
        """Initialize the repository."""
        super().__init__(MongoDB.get_collection("users"))
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def _map_to_model(self, db_item: Dict[str, Any]) -> Optional[User]:
        """Map database item to User model."""
        if not db_item:
            return None
            
        # Convert _id to string
        db_item["id"] = str(db_item.pop("_id"))
        
        # Create User object
        return User(**db_item)
    
    def _convert_to_dict(self, item: UserCreate) -> Dict[str, Any]:
        """Convert UserCreate to dictionary for database operations."""
        # Convert model to dict
        item_dict = item.dict(exclude_none=True)
        
        # Rename password field to password_hash if present
        if "password" in item_dict:
            password = item_dict.pop("password")
            item_dict["password_hash"] = self.pwd_context.hash(password)
        
        # Add created_at and updated_at if not present
        now = datetime.utcnow()
        if "created_at" not in item_dict:
            item_dict["created_at"] = now
        if "updated_at" not in item_dict:
            item_dict["updated_at"] = now
            
        return item_dict
    
    def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by email."""
        try:
            result = self.collection.find_one({"email": email})
            return self._map_to_model(result) if result else None
        except Exception as e:
            print(f"Error finding user by email: {e}")
            return None
    
    def create_user(self, user_create: UserCreate) -> Optional[User]:
        """Create a new user with hashed password."""
        try:
            # Check if user already exists
            existing_user = self.find_by_email(user_create.email)
            if existing_user:
                return None
            
            # Create user
            return self.create(user_create)
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[User]:
        """Update a user."""
        try:
            update_data = user_update.dict(exclude_unset=True)
            
            # Hash the password if provided
            if "password" in update_data:
                password = update_data.pop("password")
                update_data["password_hash"] = self.pwd_context.hash(password)
            
            update_data["updated_at"] = datetime.utcnow()
            
            return self.update(user_id, update_data)
        except Exception as e:
            print(f"Error updating user: {e}")
            return None
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user by email and password."""
        try:
            user = self.find_by_email(email)
            if not user or not self.pwd_context.verify(password, user.password_hash):
                return None
            
            return user
        except Exception as e:
            print(f"Error authenticating user: {e}")
            return None 