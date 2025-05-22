"""
Hash utilities for generating and verifying hashes.
Provides functions for file integrity, checksums, and cryptographic hashing.
"""

import hashlib
import base64
import json
import os
import hmac
from pathlib import Path
from typing import Union, Dict, Any, Optional

from src.core.config import settings


def hash_file(file_path: Union[str, Path], algorithm: str = 'sha256', chunk_size: int = 4096) -> str:
    """
    Generate a hash of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (md5, sha1, sha256, sha512)
        chunk_size: Size of chunks to read at a time
        
    Returns:
        Hex string representation of the hash
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = getattr(hashlib, algorithm)()
    
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(chunk_size), b''):
            hash_func.update(chunk)
            
    return hash_func.hexdigest()


def hash_string(data: str, algorithm: str = 'sha256') -> str:
    """
    Generate a hash of a string.
    
    Args:
        data: String data to hash
        algorithm: Hash algorithm to use (md5, sha1, sha256, sha512)
        
    Returns:
        Hex string representation of the hash
    """
    hash_func = getattr(hashlib, algorithm)()
    hash_func.update(data.encode())
    return hash_func.hexdigest()


def hash_json(data: Dict[str, Any], algorithm: str = 'sha256') -> str:
    """
    Generate a hash of a JSON-serializable object.
    
    Args:
        data: Dictionary to hash
        algorithm: Hash algorithm to use (md5, sha1, sha256, sha512)
        
    Returns:
        Hex string representation of the hash
    """
    # Sort keys for consistent hashing
    json_str = json.dumps(data, sort_keys=True)
    return hash_string(json_str, algorithm)


def verify_file_hash(file_path: Union[str, Path], expected_hash: str, algorithm: str = 'sha256') -> bool:
    """
    Verify a file's hash against an expected value.
    
    Args:
        file_path: Path to the file
        expected_hash: Expected hash value
        algorithm: Hash algorithm to use (md5, sha1, sha256, sha512)
        
    Returns:
        True if the hash matches, False otherwise
    """
    actual_hash = hash_file(file_path, algorithm)
    return actual_hash.lower() == expected_hash.lower()


def generate_hmac(data: str, secret_key: str, algorithm: str = 'sha256') -> str:
    """
    Generate an HMAC for a string using a secret key.
    
    Args:
        data: String data to sign
        secret_key: Secret key for HMAC
        algorithm: Hash algorithm to use (md5, sha1, sha256, sha512)
        
    Returns:
        Base64 encoded HMAC
    """
    key = secret_key.encode()
    message = data.encode()
    
    hmac_digest = hmac.new(key, message, getattr(hashlib, algorithm)).digest()
    return base64.b64encode(hmac_digest).decode()


def verify_hmac(data: str, hmac_value: str, secret_key: str, algorithm: str = 'sha256') -> bool:
    """
    Verify an HMAC for a string.
    
    Args:
        data: String data to verify
        hmac_value: Base64 encoded HMAC to verify against
        secret_key: Secret key for HMAC
        algorithm: Hash algorithm to use (md5, sha1, sha256, sha512)
        
    Returns:
        True if the HMAC is valid, False otherwise
    """
    calculated_hmac = generate_hmac(data, secret_key, algorithm)
    return hmac.compare_digest(calculated_hmac, hmac_value)


def hash_password(password: str) -> str:
    """
    Create a secure hash of a password.
    Uses SHA-256 with a random salt and the application's HASH_PASSWORD_KEY for added security.
    
    Args:
        password: The password to hash
        
    Returns:
        Hashed password string (includes algorithm, salt, and hash)
    """
    salt = os.urandom(32)
    
    # Get the application's hash password key or use a default if not set
    hash_key = getattr(settings, 'HASH_PASSWORD_KEY', '')
    
    if hash_key:
        # Add the hash key to the password for extra security
        password = f"{password}{hash_key}"
    
    pw_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'), 
        salt, 
        100000
    )
    
    # Format: algorithm$salt$hash
    return f"pbkdf2:sha256:100000${base64.b64encode(salt).decode()}${base64.b64encode(pw_hash).decode()}"


def verify_password(stored_password: str, provided_password: str) -> bool:
    """
    Verify a password against its stored hash.
    
    Args:
        stored_password: The stored password hash
        provided_password: The password to verify
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        # Parse the stored password hash
        parts = stored_password.split('$')
        
        if len(parts) != 3:
            # Old format might have fewer segments or malformed hash
            print(f"Invalid hash format: {stored_password}, parts: {len(parts)}")
            return False
            
        algorithm, salt_b64, hash_b64 = parts
        
        # Extract algorithm and iterations
        algo_parts = algorithm.split(':')
        if len(algo_parts) == 3:
            _, hash_name, iterations_str = algo_parts
            iterations = int(iterations_str)
        else:
            hash_name = 'sha256'
            iterations = 100000
        
        # Decode salt and hash
        try:
            salt = base64.b64decode(salt_b64)
            stored_hash = base64.b64decode(hash_b64)
        except Exception as e:
            print(f"Error decoding salt or hash: {e}")
            return False
        
        # Get the application's hash password key or use a default if not set
        hash_key = getattr(settings, 'HASH_PASSWORD_KEY', '')
        
        if hash_key:
            # Add the hash key to the password for extra security
            provided_password = f"{provided_password}{hash_key}"
        
        # Calculate hash of provided password
        computed_hash = hashlib.pbkdf2_hmac(
            hash_name,
            provided_password.encode('utf-8'),
            salt,
            iterations
        )
        
        # Compare in constant time to prevent timing attacks
        return hmac.compare_digest(stored_hash, computed_hash)
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False


def compute_file_checksum(file_path: Union[str, Path], algorithm: str = 'md5') -> str:
    """
    Compute a checksum for a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (md5, sha1, sha256)
        
    Returns:
        Hex string representation of the checksum
    """
    return hash_file(file_path, algorithm)


def hash_binary(data: bytes, algorithm: str = 'sha256') -> str:
    """
    Generate a hash of binary data.
    
    Args:
        data: Binary data to hash
        algorithm: Hash algorithm to use (md5, sha1, sha256, sha512)
        
    Returns:
        Hex string representation of the hash
    """
    hash_func = getattr(hashlib, algorithm)()
    hash_func.update(data)
    return hash_func.hexdigest() 

