"""
Bcrypt password service implementation.
"""

import logging
from typing import Optional

from services.authentication.core.interfaces import PasswordService
from utils.hash import hash_password, verify_password
logger = logging.getLogger(__name__)

class BcryptPasswordService(PasswordService):
    """Bcrypt implementation of password service."""
    
    def __init__(self, rounds: int = 12):
        """
        Initialize the bcrypt password service.
        
        Args:
            rounds: Number of hashing rounds, higher is more secure but slower
        """
        self.rounds = rounds
        logger.info(f"Initialized BcryptPasswordService with {rounds} rounds")
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        try:
            hashed_password = hash_password(password)
            return hashed_password
        except Exception as e:
            logger.error(f"Error hashing password: {e}")
            # In case of error, still return something that won't match
            return f"__error__{str(e)}"
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash using bcrypt.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            # Handle error cases in hashed_password
            if hashed_password.startswith("__error__"):
                return False
            # Verify the password against the hash
            return verify_password(hashed_password, plain_password)
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False 