"""
JWT-based authentication service implementation.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from services.authentication.core.interfaces import AuthenticationService, TokenService, PasswordService
from repositories.user_repository import UserRepository
from models.user import User, UserCreate

logger = logging.getLogger(__name__)

class JWTAuthService(AuthenticationService):
    """JWT-based authentication service implementation."""
    
    def __init__(
        self, 
        user_repository: UserRepository,
        token_service: TokenService,
        password_service: PasswordService
    ):
        """
        Initialize the JWT authentication service.
        
        Args:
            user_repository: Repository for user data
            token_service: Service for token operations
            password_service: Service for password operations
        """
        self.user_repository = user_repository
        self.token_service = token_service
        self.password_service = password_service
        logger.info("Initialized JWT Authentication Service")
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: Username or email of the user
            password: User's password
            
        Returns:
            User object if authentication is successful, None otherwise
        """
        try:
            # Find user by email or username
            user = self.user_repository.find_by_email(username)
            
            # If user not found, try to find by username if repository supports it
            if not user and hasattr(self.user_repository, 'find_by_username'):
                user = self.user_repository.find_by_username(username)
                
            if not user:
                logger.warning(f"User not found: {username}")
                return None
                
            # Verify password
            if not self.verify_password(password, user.password_hash):
                logger.warning(f"Invalid password for user: {username}")
                return None
                
            logger.info(f"User authenticated: {username}")
            return user
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    def get_current_user(self, token: str) -> Optional[User]:
        """
        Get the current user from a token.
        
        Args:
            token: JWT token
            
        Returns:
            User object if token is valid, None otherwise
        """
        try:
            # Decode token
            payload = self.token_service.decode_token(token)
            if not payload:
                logger.warning("Invalid token")
                return None
                
            user_id = payload.get("sub")
            if not user_id:
                logger.warning("Token missing user ID")
                return None
                
            # Get user by ID
            user = self.user_repository.find_by_id(user_id)
            if not user:
                logger.warning(f"User not found: {user_id}")
                return None
                
            return user
            
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            return None
    
    def register_user(self, user_data: UserCreate) -> Optional[User]:
        """
        Register a new user.
        
        Args:
            user_data: User registration data
            
        Returns:
            Newly created user object if registration is successful, None otherwise
        """
        try:
            # Check if user already exists
            existing_user = self.user_repository.find_by_email(user_data.email)
            if existing_user:
                logger.warning(f"User already exists: {user_data.email}")
                return None
                
            # Hash password
            hashed_password = self.password_service.hash_password(user_data.password)
            
            # Create user with hashed password
            user_create = UserCreate(
                email=user_data.email,
                password=hashed_password,
                full_name=user_data.full_name,
                role=user_data.role
            )
            
            # Create user in repository
            user = self.user_repository.create_user(user_create)
            
            logger.info(f"User registered: {user.email}")
            return user
            
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return None
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[int] = None) -> str:
        """
        Create a new JWT access token.
        
        Args:
            data: Data to include in the token
            expires_delta: Optional token expiration time in seconds
            
        Returns:
            JWT token string
        """
        return self.token_service.create_access_token(data, expires_delta)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        return self.password_service.verify_password(plain_password, hashed_password)
    
    def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """
        Change a user's password.
        
        Args:
            user_id: ID of the user
            current_password: Current password for verification
            new_password: New password to set
            
        Returns:
            True if password change is successful, False otherwise
        """
        try:
            # Get user
            user = self.user_repository.find_by_id(user_id)
            if not user:
                logger.warning(f"User not found: {user_id}")
                return False
                
            # Verify current password
            if not self.verify_password(current_password, user.password):
                logger.warning(f"Invalid current password for user: {user_id}")
                return False
                
            # Hash new password
            hashed_password = self.password_service.hash_password(new_password)
            
            # Update user password
            success = self.user_repository.update_password(user_id, hashed_password)
            
            if success:
                logger.info(f"Password changed for user: {user_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error changing password: {e}")
            return False
    
    def get_permissions(self, user_id: str) -> List[str]:
        """
        Get a user's permissions.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of permission strings
        """
        try:
            # Get user
            user = self.user_repository.find_by_id(user_id)
            if not user:
                logger.warning(f"User not found: {user_id}")
                return []
                
            # If repository has a get_permissions method, use it
            if hasattr(self.user_repository, 'get_permissions'):
                return self.user_repository.get_permissions(user_id)
                
            # Otherwise, derive permissions from role
            # This is a simple implementation - in a real app, you'd have a more complex permissions system
            if not hasattr(user, 'role'):
                return []
                
            role = user.role.lower() if user.role else ""
            
            if role == "admin":
                return ["users:read", "users:write", "proposals:read", "proposals:write", "emails:read", "emails:write"]
            elif role == "manager":
                return ["proposals:read", "proposals:write", "emails:read"]
            elif role == "user":
                return ["proposals:read", "emails:read"]
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting permissions: {e}")
            return []
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Check the health status of the authentication service.
        
        Returns:
            Dictionary with status information
        """
        status = {
            "auth_service": "healthy",
            "token_service": "unknown",
            "password_service": "unknown",
            "user_repository": "unknown",
            "last_checked": datetime.utcnow().isoformat()
        }
        
        # Check token service
        try:
            # Simple check - try to create a token
            test_token = self.token_service.create_access_token({"test": "data"}, 60)
            if test_token:
                status["token_service"] = "healthy"
            else:
                status["token_service"] = "error"
        except Exception as e:
            status["token_service"] = f"error: {str(e)}"
            
        # Check password service
        try:
            # Simple check - try to hash a password
            test_hash = self.password_service.hash_password("test")
            if test_hash and self.password_service.verify_password("test", test_hash):
                status["password_service"] = "healthy"
            else:
                status["password_service"] = "error"
        except Exception as e:
            status["password_service"] = f"error: {str(e)}"
            
        # Check user repository
        try:
            # Check if repository is accessible
            if self.user_repository:
                status["user_repository"] = "healthy"
        except Exception as e:
            status["user_repository"] = f"error: {str(e)}"
            
        return status 