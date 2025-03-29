#!/usr/bin/env python
# Setup Gmail API Authentication
import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

def setup_gmail_auth():
    """Setup Gmail API authentication."""
    
    print("Gmail API Authentication Setup")
    print("==============================")
    print("This script will guide you through setting up Gmail API authentication.")
    print("Before running this script, make sure you have:")
    print("1. Created a project in Google Cloud Console")
    print("2. Enabled the Gmail API")
    print("3. Created OAuth client ID credentials")
    print("4. Downloaded the credentials.json file")
    print("\n")
    
    # Get credentials file path
    creds_path = input("Enter the path to your credentials.json file [./credentials.json]: ") or "./credentials.json"
    
    if not os.path.exists(creds_path):
        print(f"Error: Could not find credentials file at {creds_path}")
        return
    
    # Create token file
    token_path = input("Enter the path to save the token.json file [./token.json]: ") or "./token.json"
    
    # Get Gmail API access
    try:
        # The file token.json stores the user's access and refresh tokens
        creds = None
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_info(
                json.load(open(token_path))
            )
            
        # If there are no valid credentials, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    creds_path, 
                    ['https://www.googleapis.com/auth/gmail.modify']
                )
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
                
        print("\nGmail API authentication successful!")
        print(f"Token saved to {token_path}")
        print("\nNow you can update your .env file with:")
        print(f"GMAIL_CREDENTIALS_PATH=\"{os.path.abspath(creds_path)}\"")
        print(f"GMAIL_TOKEN_PATH=\"{os.path.abspath(token_path)}\"")
        
    except Exception as e:
        print(f"Error setting up Gmail API authentication: {str(e)}")
        
if __name__ == "__main__":
    setup_gmail_auth() 