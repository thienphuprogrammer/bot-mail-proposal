#!/usr/bin/env python
"""
Script to generate a secure encryption key and update the .env file.
Run this script to create a new encryption key.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to import from src
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from src.utils.crypto import generate_encryption_key

def update_env_file(key):
    """Update the .env file with the new key."""
    env_path = Path('../.env')
    
    if not env_path.exists():
        # Create .env file if it doesn't exist
        with open(env_path, 'w') as f:
            f.write(f"ENCRYPTION_KEY={key}\n")
        print(f"Created new .env file with ENCRYPTION_KEY")
        return
    
    # Read existing .env file
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    key_exists = False
    new_lines = []
    
    # Replace or add the key
    for line in lines:
        if line.startswith('ENCRYPTION_KEY='):
            new_lines.append(f"ENCRYPTION_KEY={key}\n")
            key_exists = True
        else:
            new_lines.append(line)
    
    if not key_exists:
        new_lines.append(f"ENCRYPTION_KEY={key}\n")
    
    # Write back to .env file
    with open(env_path, 'w') as f:
        f.writelines(new_lines)
    
    print(f"Updated ENCRYPTION_KEY in .env file")

if __name__ == "__main__":
    # Generate a secure Fernet key
    key = generate_encryption_key()
    update_env_file(key)
    print(f"Generated new encryption key")
    print(f"Key: {key}")
    print("Keep this key safe! It's needed to decrypt any previously encrypted data.") 