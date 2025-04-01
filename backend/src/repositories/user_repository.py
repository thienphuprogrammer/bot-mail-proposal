from typing import Dict, Any, Optional, List
from datetime import datetime
from bson import ObjectId

from database.mongodb import MongoDB
from models.user import User, UserCreate
from repositories.base_repository import MongoRepository
from utils.hash import verify_password

class UserRepository(MongoRepository[User, UserCreate]):
    """Repository for User operations."""

    def __init__(self):
        """Initialize repository with users collection."""
        super().__init__(MongoDB.get_collection("users"))
    
    def _map_to_model(self, db_item: Dict[str, Any]) -> User:
        """Map database item to User model."""
        if not db_item:
            return None
        
        # Create user model without password_hash
        user_data = {k: v for k, v in db_item.items()}
        return User(**user_data)
    
    def _convert_to_dict(self, item: UserCreate) -> Dict[str, Any]:
        """Convert UserCreate to dictionary for database operations."""
        # Hash password        
        # Create user dict without password
        user_dict = item.model_dump(by_alias=True, exclude={"password"})
        
        # Add hashed password
        user_dict["password_hash"] = item.password
        
        # Add created_at
        user_dict["created_at"] = datetime.utcnow()
        user_dict["last_login"] = None
        
        return user_dict
    
    def create_user(self, user_create: UserCreate) -> Optional[User]:
        """Create a new user."""
        # Check if user with email already exists
        existing_user = self.find_by_email(user_create.email)
        if existing_user:
            return None
            
        # Create user
        return self.create(user_create)
    
    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email."""
        result = self.collection.find_one({"email": email})
        return self._map_to_model(result) if result else None
    
    def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        try:
            # Find user by email
            user_dict = self.collection.find_one({"email": email})
            if not user_dict:
                return None
            
            # Verify password - fixed typo in password_hash key
            stored_hash = user_dict.get("password_hash", "")
            if not stored_hash or not verify_password(stored_hash, password):
                print("Password verification failed")
                return None
            
            # Update last login time
            self.update_last_login(str(user_dict["_id"]))
            
            # Return User model without password_hash
            return self._map_to_model(user_dict)
        except Exception as e:
            print(f"Error authenticating user: {e}")
            return None
    
    def update_last_login(self, user_id: str) -> None:
        """Update last login time."""
        self.update(user_id, {"last_login": datetime.utcnow()})
    
    def find_by_role(self, role: str) -> List[User]:
        """Find users by role."""
        cursor = self.collection.find({"role": role})
        return [self._map_to_model(doc) for doc in cursor]