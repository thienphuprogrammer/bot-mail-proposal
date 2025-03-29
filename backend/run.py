#!/usr/bin/env python
"""
Run script for the Automated Proposal Generation System.
This script provides a command-line interface to run different components.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Add the current directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_api():
    """Run the FastAPI application."""
    print("Starting FastAPI application...")
    from src.core.config import settings
    
    # Get the host and port
    host = os.environ.get("HOST", "127.0.0.1")
    port = os.environ.get("PORT", "8000")
    
    # Run uvicorn
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "src.main:app", 
        "--host", host, 
        "--port", port,
        "--reload"
    ]
    
    if settings.DEBUG:
        cmd.append("--log-level=debug")
    
    subprocess.run(cmd)

def run_streamlit():
    """Run the Streamlit application."""
    print("Starting Streamlit application...")
    
    # Run streamlit
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        "src/streamlit_app.py",
        "--server.headless", "true"
    ]
    
    subprocess.run(cmd)

def run_setup():
    """Setup the application environment."""
    print("Setting up the application environment...")
    
    # Create necessary directories
    os.makedirs("temp", exist_ok=True)
    
    # Check if .env file exists
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    if not env_path.exists() and env_example_path.exists():
        print("Creating .env file from .env.example...")
        with open(env_example_path, "r") as src, open(env_path, "w") as dst:
            dst.write(src.read())
        print("Created .env file. Please update it with your configuration.")
    
    # Check if Gmail token is needed
    gmail_script_path = Path("scripts/setup_gmail.py")
    if gmail_script_path.exists():
        setup_gmail = input("Do you want to setup Gmail API authentication? (y/n): ")
        if setup_gmail.lower() == "y":
            subprocess.run([sys.executable, str(gmail_script_path)])

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run Automated Proposal Generation System")
    
    # Add subparsers
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # API subcommand
    api_parser = subparsers.add_parser("api", help="Run the FastAPI application")
    
    # Streamlit subcommand
    streamlit_parser = subparsers.add_parser("streamlit", help="Run the Streamlit application")
    
    # Setup subcommand
    setup_parser = subparsers.add_parser("setup", help="Setup the application environment")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run the appropriate command
    if args.command == "api":
        run_api()
    elif args.command == "streamlit":
        run_streamlit()
    elif args.command == "setup":
        run_setup()
    else:
        # Default to showing help
        parser.print_help()

if __name__ == "__main__":
    main() 