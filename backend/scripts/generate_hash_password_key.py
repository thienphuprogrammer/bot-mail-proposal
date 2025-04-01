#!/usr/bin/env python
"""
Script to generate a secure hash password key and update the .env file.
Run this script to create a new hash password key.
"""

import os
import sys
import secrets
import base64
from pathlib import Path

def generate_hash_password_key(length=32):
    """Generate a secure hash password key."""
    # Generate random bytes
    random_bytes = secrets.token_bytes(length)
    
    # Encode as base64 for storage
    encoded_key = base64.urlsafe_b64encode(random_bytes).decode('utf-8')
    
    return encoded_key

def update_env_file(key):
    """Update the .env file with the new key."""
    env_path = Path('.env')
    
    if not env_path.exists():
        # Create .env file if it doesn't exist
        with open(env_path, 'w') as f:
            f.write(f"HASH_PASSWORD_KEY={key}\n")
        print(f"Created new .env file with HASH_PASSWORD_KEY")
        return
    
    # Read existing .env file
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    key_exists = False
    new_lines = []
    
    # Replace or add the key
    for line in lines:
        if line.startswith('HASH_PASSWORD_KEY='):
            new_lines.append(f"HASH_PASSWORD_KEY={key}\n")
            key_exists = True
        else:
            new_lines.append(line)
    
    if not key_exists:
        new_lines.append(f"HASH_PASSWORD_KEY={key}\n")
    
    # Write back to .env file
    with open(env_path, 'w') as f:
        f.writelines(new_lines)
    
    print(f"Updated HASH_PASSWORD_KEY in .env file")

if __name__ == "__main__":
    # Generate a secure hash password key
    key = generate_hash_password_key()
    update_env_file(key)
    print(f"Generated new hash password key")
    print(f"Key: {key}")
    print("IMPORTANT: This will affect all future password hashes. Existing passwords will need to be rehashed with this key.") 