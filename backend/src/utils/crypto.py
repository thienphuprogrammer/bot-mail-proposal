"""
Cryptography utilities for secure handling of sensitive data.
Provides encryption, decryption, and key management functions.
"""

import base64
import hashlib
import hmac
import os
from typing import Tuple, Optional, Union, Dict, Any

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
    Encoding,
    PrivateFormat,
    PublicFormat,
    NoEncryption,
)
from cryptography.exceptions import InvalidSignature

# Import from core configuration
from src.core.config import settings


def generate_key(password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
    """
    Generate a key from password and salt using PBKDF2HMAC.
    
    Args:
        password: The password to derive the key from
        salt: Optional salt, will be generated if not provided
        
    Returns:
        Tuple of (key, salt)
    """
    if salt is None:
        salt = os.urandom(16)
        
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt


def encrypt_data(data: str, key: Optional[bytes] = None) -> Tuple[bytes, bytes]:
    """
    Encrypt data using Fernet symmetric encryption.
    
    Args:
        data: String data to encrypt
        key: Optional encryption key, will use settings.ENCRYPTION_KEY if not provided
        
    Returns:
        Tuple of (encrypted_data, key)
    """
    if key is None:
        # Use application encryption key from settings
        key_str = settings.ENCRYPTION_KEY
        
        # Generate a key if not configured
        if not key_str:
            print("Warning: No encryption key found in settings, generating temporary key")
            key = Fernet.generate_key()
        else:
            # Handle the key format - ensure it's properly base64 encoded
            if not key_str.endswith('=') and len(key_str) % 4 != 0:
                # Add padding if needed
                key_str = key_str + '=' * (4 - len(key_str) % 4)
                
            try:
                # Try to use the key directly
                key = key_str.encode() if isinstance(key_str, str) else key_str
                # Test if the key is valid by creating a Fernet instance
                Fernet(key)
            except Exception as e:
                # If not a valid Fernet key, derive one using PBKDF2
                print(f"Invalid Fernet key format, deriving key using PBKDF2: {str(e)}")
                salt = b'fixed_salt_for_app_encryption'  # Using a fixed salt for app-wide encryption
                derived_key, _ = generate_key(key_str, salt)
                key = derived_key
    
    f = Fernet(key)
    encrypted_data = f.encrypt(data.encode())
    return encrypted_data, key


def decrypt_data(encrypted_data: bytes, key: Optional[bytes] = None) -> str:
    """
    Decrypt data using Fernet symmetric encryption.
    
    Args:
        encrypted_data: The encrypted data
        key: The encryption key, will use settings.ENCRYPTION_KEY if not provided
        
    Returns:
        Decrypted string
    
    Raises:
        ValueError: If decryption fails due to invalid key or corrupted data
    """
    try:
        if key is None:
            # Use application encryption key from settings
            key_str = settings.ENCRYPTION_KEY
            
            if not key_str:
                raise ValueError("No encryption key provided and no key found in settings")
                
            # Handle the key format - ensure it's properly base64 encoded
            if not key_str.endswith('=') and len(key_str) % 4 != 0:
                # Add padding if needed
                key_str = key_str + '=' * (4 - len(key_str) % 4)
                
            try:
                # Try to use the key directly
                key = key_str.encode() if isinstance(key_str, str) else key_str
                # Test if the key is valid by creating a Fernet instance
                Fernet(key)
            except Exception as e:
                # If not a valid Fernet key, derive one using PBKDF2
                salt = b'fixed_salt_for_app_encryption'  # Same fixed salt used in encrypt_data
                derived_key, _ = generate_key(key_str, salt)
                key = derived_key
        
        f = Fernet(key)
        decrypted_data = f.decrypt(encrypted_data)
        return decrypted_data.decode()
    except InvalidToken:
        raise ValueError("Decryption failed: Invalid key or corrupted data")
    except Exception as e:
        raise ValueError(f"Decryption error: {str(e)}")


def generate_rsa_keypair(key_size: int = 2048) -> Tuple[bytes, bytes]:
    """
    Generate an RSA key pair for asymmetric encryption.
    
    Args:
        key_size: Size of the key in bits (2048, 3072, or 4096 recommended)
        
    Returns:
        Tuple of (private_key_pem, public_key_pem)
    """
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size
    )
    
    # Extract public key
    public_key = private_key.public_key()
    
    # Convert to PEM format
    private_pem = private_key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption()
    )
    
    public_pem = public_key.public_bytes(
        encoding=Encoding.PEM,
        format=PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem, public_pem


def rsa_encrypt(data: str, public_key_pem: bytes) -> bytes:
    """
    Encrypt data using RSA public key.
    
    Args:
        data: String data to encrypt
        public_key_pem: PEM encoded public key
        
    Returns:
        Encrypted data
    """
    public_key = load_pem_public_key(public_key_pem)
    
    encrypted_data = public_key.encrypt(
        data.encode(),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    return encrypted_data


def rsa_decrypt(encrypted_data: bytes, private_key_pem: bytes) -> str:
    """
    Decrypt data using RSA private key.
    
    Args:
        encrypted_data: Encrypted data
        private_key_pem: PEM encoded private key
        
    Returns:
        Decrypted string
    """
    private_key = load_pem_private_key(
        private_key_pem,
        password=None,
    )
    
    decrypted_data = private_key.decrypt(
        encrypted_data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    return decrypted_data.decode()


def rsa_sign(data: str, private_key_pem: bytes) -> bytes:
    """
    Create a digital signature using RSA private key.
    
    Args:
        data: String data to sign
        private_key_pem: PEM encoded private key
        
    Returns:
        Digital signature
    """
    private_key = load_pem_private_key(
        private_key_pem,
        password=None,
    )
    
    signature = private_key.sign(
        data.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    
    return signature


def rsa_verify(data: str, signature: bytes, public_key_pem: bytes) -> bool:
    """
    Verify a digital signature using RSA public key.
    
    Args:
        data: String data that was signed
        signature: Digital signature to verify
        public_key_pem: PEM encoded public key
        
    Returns:
        True if signature is valid, False otherwise
    """
    public_key = load_pem_public_key(public_key_pem)
    
    try:
        public_key.verify(
            signature,
            data.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except InvalidSignature:
        return False


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a secure random token.
    
    Args:
        length: Length of the token in bytes
        
    Returns:
        Base64 encoded token string
    """
    random_bytes = os.urandom(length)
    return base64.urlsafe_b64encode(random_bytes).decode('utf-8')


def generate_encryption_key() -> str:
    """
    Generate a secure encryption key suitable for Fernet encryption.
    
    Returns:
        Base64 encoded Fernet key
    """
    # Generate a Fernet key directly
    key = Fernet.generate_key()
    return key.decode('utf-8') 