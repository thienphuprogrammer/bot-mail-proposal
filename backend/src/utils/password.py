"""
Password management utilities for secure handling of passwords.
"""

import re
import random
import string
from typing import Tuple, List, Optional

from src.utils.hash import hash_password, verify_password


class PasswordManager:
    """Password management and validation utilities."""
    
    def __init__(self, 
                 min_length: int = 8, 
                 require_uppercase: bool = True,
                 require_lowercase: bool = True,
                 require_digits: bool = True,
                 require_special: bool = True):
        """
        Initialize password manager with validation rules.
        
        Args:
            min_length: Minimum password length
            require_uppercase: Whether to require uppercase letters
            require_lowercase: Whether to require lowercase letters
            require_digits: Whether to require digits
            require_special: Whether to require special characters
        """
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_special = require_special
    
    def validate_password(self, password: str) -> Tuple[bool, List[str]]:
        """
        Validate a password against security rules.
        
        Args:
            password: The password to validate
            
        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors = []
        
        # Check length
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long")
        
        # Check for uppercase letters
        if self.require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Check for lowercase letters
        if self.require_lowercase and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        # Check for digits
        if self.require_digits and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")
        
        # Check for special characters
        if self.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
    
    def generate_password(self, length: int = 16) -> str:
        """
        Generate a secure random password.
        
        Args:
            length: Length of the password
            
        Returns:
            Secure random password string
        """
        if length < self.min_length:
            length = self.min_length
            
        # Character pools
        uppercase = string.ascii_uppercase
        lowercase = string.ascii_lowercase
        digits = string.digits
        special = '!@#$%^&*(),.?":{}|<>'
        
        # Ensure at least one character from each required group
        password = []
        
        if self.require_uppercase:
            password.append(random.choice(uppercase))
        
        if self.require_lowercase:
            password.append(random.choice(lowercase))
        
        if self.require_digits:
            password.append(random.choice(digits))
        
        if self.require_special:
            password.append(random.choice(special))
        
        # Generate remaining characters
        all_chars = ""
        if self.require_uppercase:
            all_chars += uppercase
        if self.require_lowercase:
            all_chars += lowercase
        if self.require_digits:
            all_chars += digits
        if self.require_special:
            all_chars += special
            
        # Fill to required length
        remaining = length - len(password)
        password.extend(random.choice(all_chars) for _ in range(remaining))
        
        # Shuffle the password
        random.shuffle(password)
        
        return ''.join(password)
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password securely.
        
        Args:
            password: The password to hash
            
        Returns:
            Hashed password
        """
        return hash_password(password)
    
    def verify_password(self, stored_password: str, provided_password: str) -> bool:
        """
        Verify a password against its stored hash.
        
        Args:
            stored_password: The stored password hash
            provided_password: The password to verify
            
        Returns:
            True if password matches, False otherwise
        """
        return verify_password(stored_password, provided_password)
    
    def password_strength(self, password: str) -> Tuple[str, float]:
        """
        Evaluate password strength.
        
        Args:
            password: The password to evaluate
            
        Returns:
            Tuple of (strength_category, strength_score)
            where strength_category is one of: "very weak", "weak", "moderate", "strong", "very strong"
            and strength_score is a value between 0.0 and 1.0
        """
        score = 0.0
        length = len(password)
        
        # Base score from length
        if length >= 16:
            score += 0.25
        elif length >= 12:
            score += 0.2
        elif length >= 8:
            score += 0.1
        else:
            score += 0.05
            
        # Character diversity
        if any(c.isupper() for c in password):
            score += 0.15
        if any(c.islower() for c in password):
            score += 0.15
        if any(c.isdigit() for c in password):
            score += 0.15
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 0.15
            
        # Variety score
        char_types = sum([
            any(c.isupper() for c in password),
            any(c.islower() for c in password),
            any(c.isdigit() for c in password),
            bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        ])
        
        score += char_types * 0.05
        
        # Cap at 1.0
        score = min(score, 1.0)
        
        # Map score to category
        if score >= 0.8:
            category = "very strong"
        elif score >= 0.6:
            category = "strong"
        elif score >= 0.4:
            category = "moderate"
        elif score >= 0.2:
            category = "weak"
        else:
            category = "very weak"
            
        return category, score


# Create a default instance with standard settings
password_manager = PasswordManager() 