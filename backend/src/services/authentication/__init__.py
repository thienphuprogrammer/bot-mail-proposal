"""
Authentication Service Package
===========================

A comprehensive authentication system that handles user authentication, JWT tokens,
and password management. The architecture follows a clean separation of concerns
with dependency injection for better testability.

Directory Structure:
- core/: Core interfaces and service orchestration
- providers/: Authentication implementations

Usage Example:
    ```python
    from src.services.authentication import create_auth_service
    from src.repositories.user_repository import UserRepository
    
    # Set up repository
    user_repo = UserRepository()
    
    # Get a configured authentication service
    auth_service = create_auth_service(user_repository=user_repo)
    
    # Use the service
    user = auth_service.authenticate_user("user@example.com", "password123")
    if user:
        token = auth_service.create_access_token({"sub": str(user.id)})
        print(f"Authenticated! Token: {token}")
    ```
"""

# Export core interfaces and classes
from src.services.authentication.core import (
    AuthenticationService,
    TokenService,
    PasswordService,
    AuthServiceFactory,
)

# Export provider implementations
from src.services.authentication.providers import (
    JWTAuthService,
    JWTTokenService,
    BcryptPasswordService,
)

# Convenient factory function
def create_auth_service(user_repository: any) -> AuthenticationService:
    """
    Create a default authentication service with all necessary components.
    
    Args:
        user_repository: Repository for user data
        
    Returns:
        A configured authentication service ready for user operations
    """
    return AuthServiceFactory.create_default_auth_service(user_repository=user_repository)

__all__ = [
    # Core interfaces
    "AuthenticationService",
    "TokenService",
    "PasswordService",
    
    # Implementation classes
    "JWTAuthService",
    "JWTTokenService", 
    "BcryptPasswordService",
    
    # Factory
    "AuthServiceFactory",
    
    # Helper functions
    "create_auth_service",
]
