"""
Authentication Service Interfaces
===============================

This module defines the core interfaces that all authentication service implementations must follow.
The design uses the Interface Segregation Principle to separate different concerns.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict, List

class AuthenticationService(ABC):
    """Base interface for authentication services."""
    
    @abstractmethod
    def authenticate_user(self, username: str, password: str) -> Optional[Any]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: Username or email of the user
            password: User's password
            
        Returns:
            User object if authentication is successful, None otherwise
        """
        pass
    
    @abstractmethod
    def get_current_user(self, token: str) -> Optional[Any]:
        """
        Get the current user from a token.
        
        Args:
            token: JWT token or session token
            
        Returns:
            User object if token is valid, None otherwise
        """
        pass
    
    @abstractmethod
    def register_user(self, user_data: Any) -> Optional[Any]:
        """
        Register a new user.
        
        Args:
            user_data: User registration data
            
        Returns:
            Newly created user object if registration is successful, None otherwise
        """
        pass
    
    @abstractmethod
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[int] = None) -> str:
        """
        Create a new JWT access token.
        
        Args:
            data: Data to include in the token
            expires_delta: Optional token expiration time in seconds
            
        Returns:
            JWT token string
        """
        pass
    
    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def get_permissions(self, user_id: str) -> List[str]:
        """
        Get a user's permissions.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of permission strings
        """
        pass
    
    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """
        Check the health status of the authentication service.
        
        Returns:
            Dictionary with status information
        """
        pass


class TokenService(ABC):
    """Interface for token generation and validation."""
    
    @abstractmethod
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[int] = None) -> str:
        """
        Create a new JWT access token.
        
        Args:
            data: Data to include in the token
            expires_delta: Optional token expiration time in seconds
            
        Returns:
            JWT token string
        """
        pass
    
    @abstractmethod
    def create_refresh_token(self, data: Dict[str, Any], expires_delta: Optional[int] = None) -> str:
        """
        Create a new JWT refresh token.
        
        Args:
            data: Data to include in the token
            expires_delta: Optional token expiration time in seconds
            
        Returns:
            JWT token string
        """
        pass
    
    @abstractmethod
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token to decode
            
        Returns:
            Dictionary with token payload if valid, None otherwise
        """
        pass
    
    @abstractmethod
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Generate a new access token using a refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New access token if refresh token is valid, None otherwise
        """
        pass


class PasswordService(ABC):
    """Interface for password hashing and verification."""
    
    @abstractmethod
    def hash_password(self, password: str) -> str:
        """
        Hash a password.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        pass
    
    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        pass 