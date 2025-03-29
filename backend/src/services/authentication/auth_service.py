from typing import Optional
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext

from src.core.config import settings
from src.models.user import User, UserCreate
from src.repositories.user_repository import UserRepository
from src.services.base_service import AuthenticationService

class AuthService(AuthenticationService):
    """Service for user authentication."""
    
    def __init__(self, user_repository: UserRepository):
        """Initialize the auth service."""
        self.user_repository = user_repository
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password."""
        try:
            # Find user by email
            user = self.user_repository.find_by_email(username)
            
            # If user not found or password doesn't match
            if not user or not self.verify_password(password, user.password_hash):
                return None
            
            return user
        except Exception as e:
            print(f"Error authenticating user: {e}")
            return None
    
    def create_access_token(self, user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token for a user."""
        try:
            # Set expiration time
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
            
            # Create token payload
            payload = {
                "sub": user_id,
                "exp": expire
            }
            
            # Encode token
            encoded_jwt = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
            
            return encoded_jwt
        except Exception as e:
            print(f"Error creating access token: {e}")
            raise
    
    def get_current_user(self, token: str) -> Optional[User]:
        """Get the current user from a token."""
        try:
            # Decode token
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
            user_id = payload.get("sub")
            
            if not user_id:
                return None
            
            # Get user by ID
            user = self.user_repository.find_by_id(user_id)
            
            return user
        except jwt.PyJWTError as e:
            print(f"JWT error: {e}")
            return None
        except Exception as e:
            print(f"Error getting current user: {e}")
            return None
    
    def register_user(self, user_data: UserCreate) -> Optional[User]:
        """Register a new user."""
        try:
            # Check if user already exists
            existing_user = self.user_repository.find_by_email(user_data.email)
            if existing_user:
                return None
            
            # Hash password
            hashed_password = self.get_password_hash(user_data.password)
            
            # Create user
            user = self.user_repository.create_user(
                UserCreate(
                    email=user_data.email,
                    password=hashed_password,
                    full_name=user_data.full_name,
                    role=user_data.role
                )
            )
            
            return user
        except Exception as e:
            print(f"Error registering user: {e}")
            return None
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Get password hash."""
        return self.pwd_context.hash(password) 