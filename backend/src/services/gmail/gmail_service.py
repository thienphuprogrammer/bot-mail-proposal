import os
import base64
from typing import List, Optional
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from src.models.email import Email
from src.services.gmail.base_gmail import EmailService
from src.core.config import settings

class GmailService(EmailService):
    """Service for Gmail operations."""
    
    def __init__(self):
        """Initialize the Gmail service."""
        self.service = self._get_service()
    
    def _get_service(self):
        """Get the Gmail service client."""
        creds = None
        # The file token.json stores the user's access and refresh tokens
        if os.path.exists(settings.GMAIL_TOKEN_PATH):
            creds = Credentials.from_authorized_user_info(
                json.load(open(settings.GMAIL_TOKEN_PATH))
            )
        
        # If there are no valid credentials, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    settings.GMAIL_CREDENTIALS_PATH, 
                    ['https://www.googleapis.com/auth/gmail.modify']
                )
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(settings.GMAIL_TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())
        
        return build('gmail', 'v1', credentials=creds)
    
    def fetch_emails(self, query: str = "is:unread", max_results: int = 10) -> List[Email]:
        """Fetch emails based on query."""
        try:
            # Get emails matching query
            results = self.service.users().messages().list(
                userId='me', q=query, maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me', id=message['id'], format='full'
                ).execute()
                
                # Extract headers
                headers = msg['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                from_email = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
                date = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'Unknown')
                
                # Extract body
                body = self._get_email_body(msg)
                
                # Create Email object
                email = Email(
                    id=message['id'],
                    subject=subject,
                    from_email=from_email,
                    date=date,
                    body=body,
                    read=False
                )
                
                emails.append(email)
            
            return emails
        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []
    
    def mark_as_read(self, email_id: str) -> bool:
        """Mark email as read."""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except Exception as e:
            print(f"Error marking email as read: {e}")
            return False
    
    def send_email(self, to: str, subject: str, body: str, 
                   attachment_path: Optional[str] = None) -> bool:
        """Send email with optional attachment."""
        try:
            # Create message
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            
            # Add body
            msg = MIMEText(body, 'html')
            message.attach(msg)
            
            # Add attachment if provided
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as f:
                    attachment = MIMEApplication(f.read(), _subtype='pdf')
                    attachment.add_header('Content-Disposition', 'attachment', 
                                         filename=os.path.basename(attachment_path))
                    message.attach(attachment)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Send message
            self.service.users().messages().send(
                userId='me', body={'raw': raw_message}
            ).execute()
            
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def _get_email_body(self, message):
        """Extract email body from message."""
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    body = part.get('body', {})
                    data = body.get('data', '')
                    if data:
                        return base64.urlsafe_b64decode(data).decode()
        
        # Fallback to getting body from the payload body
        body = message['payload'].get('body', {})
        data = body.get('data', '')
        if data:
            return base64.urlsafe_b64decode(data).decode()
        
        return "No body found" 