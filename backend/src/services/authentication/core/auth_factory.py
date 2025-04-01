"""
Factory for creating authentication service components with proper dependency injection.
"""

import logging
from typing import Optional

from services.authentication.core.interfaces import AuthenticationService, TokenService, PasswordService
from services.authentication.providers.jwt_auth_service import JWTAuthService
from services.authentication.providers.jwt_token_service import JWTTokenService
from services.authentication.providers.bcrypt_password_service import BcryptPasswordService
from repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

class AuthServiceFactory:
    """Factory for creating authentication service components."""
    
    @staticmethod
    def create_token_service(secret_key: Optional[str] = None) -> TokenService:
        """
        Create and configure a token service.
        
        Args:
            secret_key: Optional secret key for token signing
            
        Returns:
            Configured TokenService instance
        """
        logger.info("Creating JWT token service")
        return JWTTokenService(secret_key=secret_key)
    
    @staticmethod
    def create_password_service(rounds: int = 12) -> PasswordService:
        """
        Create and configure a password service.
        
        Args:
            rounds: Number of hashing rounds
            
        Returns:
            Configured PasswordService instance
        """
        logger.info(f"Creating bcrypt password service with {rounds} rounds")
        return BcryptPasswordService(rounds=rounds)
    
    @staticmethod
    def create_auth_service(
        user_repository: UserRepository,
        token_service: Optional[TokenService] = None,
        password_service: Optional[PasswordService] = None
    ) -> AuthenticationService:
        """
        Create a complete authentication service with all dependencies.
        
        Args:
            user_repository: Repository for user data
            token_service: Optional token service
            password_service: Optional password service
            
        Returns:
            Configured AuthenticationService instance
        """
        # Create components if not provided
        if token_service is None:
            token_service = AuthServiceFactory.create_token_service()
            
        if password_service is None:
            password_service = AuthServiceFactory.create_password_service()
        
        # Create and return the authentication service
        logger.info("Creating JWT authentication service")
        return JWTAuthService(
            user_repository=user_repository,
            token_service=token_service,
            password_service=password_service
        )
    
    @staticmethod
    def create_default_auth_service(user_repository: UserRepository) -> AuthenticationService:
        """
        Create a default authentication service with all necessary components.
        
        Args:
            user_repository: Repository for user data
            
        Returns:
            Ready-to-use authentication service
        """
        return AuthServiceFactory.create_auth_service(user_repository=user_repository) 