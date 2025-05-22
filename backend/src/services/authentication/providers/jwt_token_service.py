"""
JWT token service implementation.
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from src.services.authentication.core.interfaces import TokenService
from src.core.config import settings

class JWTTokenService(TokenService):
    """JWT implementation of token service."""
    
    def __init__(self, secret_key: str = None, algorithm: str = "HS256"):
        """
        Initialize the JWT token service.
        
        Args:
            secret_key: Secret key for JWT signing, defaults to settings.JWT_SECRET
            algorithm: Algorithm for JWT signing, defaults to HS256
        """
        self.secret_key = secret_key or settings.JWT_SECRET
        self.algorithm = algorithm
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[int] = None) -> str:
        """
        Create a new JWT access token.
        
        Args:
            data: Data to include in the token
            expires_delta: Optional token expiration time in seconds
            
        Returns:
            JWT token string
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any], expires_delta: Optional[int] = None) -> str:
        """
        Create a new JWT refresh token.
        
        Args:
            data: Data to include in the token
            expires_delta: Optional token expiration time in seconds
            
        Returns:
            JWT token string
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({"exp": expire, "token_type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        return encoded_jwt
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token to decode
            
        Returns:
            Dictionary with token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.PyJWTError:
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Generate a new access token using a refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New access token if refresh token is valid, None otherwise
        """
        try:
            payload = self.decode_token(refresh_token)
            if not payload:
                return None
                
            # Verify this is a refresh token
            if payload.get("token_type") != "refresh":
                return None
                
            # Remove token_type and exp from the data for the new access token
            data = {k: v for k, v in payload.items() if k not in ["token_type", "exp"]}
            
            # Create new access token
            return self.create_access_token(data)
            
        except Exception:
            return None 