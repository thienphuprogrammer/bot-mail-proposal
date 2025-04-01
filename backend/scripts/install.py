#!/usr/bin/env python
"""
Installation script for the Automated Proposal Generation System.
"""

import subprocess
import sys
import os
import platform

def install_dependencies():
    """Install dependencies from requirements.txt."""
    
    print("Installing dependencies for Automated Proposal Generation System")
    print("==============================================================")
    
    # Get the requirements file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    req_path = os.path.join(os.path.dirname(script_dir), "requirements.txt")
    
    if not os.path.exists(req_path):
        print(f"Error: Could not find requirements.txt at {req_path}")
        return False
    
    try:
        # Check if running in virtual environment
        in_venv = sys.prefix != sys.base_prefix
        if not in_venv:
            print("Warning: It is recommended to install dependencies in a virtual environment.")
            confirm = input("Continue with installation? (y/n): ")
            if confirm.lower() != "y":
                print("Installation cancelled.")
                return False
        
        # Install dependencies
        print(f"Installing dependencies from {req_path}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_path])
        
        # Create necessary directories
        os.makedirs(os.path.join(os.path.dirname(script_dir), "temp"), exist_ok=True)
        os.makedirs(os.path.join(os.path.dirname(script_dir), "credential"), exist_ok=True)
        
        print("\nDependencies installed successfully!")
        print("\nNext steps:")
        print("1. Set up Gmail API credentials:")
        print(f"   python {os.path.join(script_dir, 'setup_gmail.py')}")
        print("2. Configure your .env file")
        print("3. Run the application:")
        print(f"   python {os.path.join(os.path.dirname(script_dir), 'run.py')} streamlit")
        
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False

if __name__ == "__main__":
    install_dependencies() 