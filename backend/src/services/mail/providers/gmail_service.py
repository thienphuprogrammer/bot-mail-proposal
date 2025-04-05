"""
Gmail service implementation that uses the Gmail API.
"""

import os
import base64
import json
import time
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from models.email import Email, EmailCreate
from services.mail.core.interfaces import BaseMailService
from services.mail.processors.gmail_processor import GmailMailProcessor
from core.config import settings
from models.proposal import ExtractedData
logger = logging.getLogger(__name__)

class GmailService(BaseMailService):
    """Gmail service implementation."""
    
    # Gmail API scopes
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
    
    # Default email query parameters
    DEFAULT_QUERY_PARAMS = {
        "max_results": 100,
        "include_spam_trash": True,
        "label_ids": ["INBOX"],
        "query": "is:unread",
        "only_recent": False  # Only emails from the last 7 days
    }
    
    def __init__(self):
        """Initialize the Gmail service."""
        self.service = self._get_service()
        
        # Create cache directory if it doesn't exist
        os.makedirs(os.path.join("temp"), exist_ok=True)
        
        # Create a cache for message IDs to avoid redundant processing
        self._processed_ids_cache = set()
        self._cache_file = os.path.join("temp", "processed_mail_ids.json")
        self._load_processed_ids_cache()
        
        # Initialize the mail processor for content extraction
        self.processor = GmailMailProcessor(self)
    
    def _get_service(self):
        """Get the Gmail service client."""
        try:
            creds = None
            # The file token.json stores the user's access and refresh tokens
            if os.path.exists(settings.GMAIL_TOKEN_PATH):
                try:
                    creds = Credentials.from_authorized_user_info(
                        json.load(open(settings.GMAIL_TOKEN_PATH))
                    )
                except Exception as e:
                    logger.error(f"Error loading credentials: {e}")
            
            # If there are no valid credentials, let the user log in
            if creds and creds.valid:
                pass
            elif creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Error refreshing credentials: {e}")
                    creds = None
            
            if not creds or not creds.valid:
                flow = InstalledAppFlow.from_client_secrets_file(
                    settings.GMAIL_CREDENTIALS_PATH, 
                    self.SCOPES
                )
                creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open(settings.GMAIL_TOKEN_PATH, 'w') as token:
                    token.write(creds.to_json())
            
            return build('gmail', 'v1', credentials=creds)
        except Exception as e:
            logger.error(f"Failed to build Gmail service: {e}")
            return None
    
    def _load_processed_ids_cache(self):
        """Load the cache of processed email IDs."""
        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, 'r') as f:
                    self._processed_ids_cache = set(json.load(f))
            else:
                # Ensure directory exists
                os.makedirs(os.path.dirname(self._cache_file), exist_ok=True)
                self._processed_ids_cache = set()
        except Exception as e:
            logger.error(f"Error loading processed IDs cache: {e}")
            self._processed_ids_cache = set()
    
    def _save_processed_ids_cache(self):
        """Save the cache of processed email IDs."""
        try:
            # Convert set to list for JSON serialization
            with open(self._cache_file, 'w') as f:
                json.dump(list(self._processed_ids_cache), f)
        except Exception as e:
            logger.error(f"Error saving processed IDs cache: {e}")
    
    def _add_to_processed_cache(self, message_id: str):
        """Add a message ID to the processed cache."""
        self._processed_ids_cache.add(message_id)
        # Periodically save the cache (not every time to reduce disk I/O)
        if len(self._processed_ids_cache) % 10 == 0:
            self._save_processed_ids_cache()
    
    def _execute_service_call(self, service_func, error_message="Error executing Gmail service call"):
        """Execute a Gmail service call with error handling."""
        if not self.service:
            logger.error("Gmail service not initialized")
            return None
            
        try:
            return service_func()
        except HttpError as e:
            logger.error(f"{error_message}: {e}")
            if e.resp.status == 401:
                logger.info("Attempting to refresh credentials...")
                self.service = self._get_service()  # Retry auth
                return None
            return None
        except Exception as e:
            logger.error(f"{error_message}: {e}")
            return None
    
    def get_health_status(self) -> Dict[str, Any]:
        """Check if the Gmail service is working properly."""
        if not self.service:
            return {
                "status": "error",
                "message": "Gmail service not initialized"
            }
            
        result = self._execute_service_call(
            lambda: self.service.users().messages().list(userId='me', maxResults=1).execute(),
            error_message="Error checking service health"
        )
        
        if result:
            return {
                "status": "ok",
                "message": "Gmail service is working",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "status": "error",
                "message": "Error connecting to Gmail service",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def fetch_emails(self, 
                     max_results: int = None, 
                     query: str = None,
                     label_ids: List[str] = None,
                     include_spam_trash: bool = None,
                     only_recent: bool = None) -> List[EmailCreate]:
        """
        Fetch emails based on query parameters.
        
        Args:
            query: Gmail search query
            max_results: Maximum number of results
            label_ids: List of label IDs to fetch from
            include_spam_trash: Whether to include spam and trash
            only_recent: If True, only fetch emails from the last 7 days
            
        Returns:
            List of EmailCreate objects
        """
        # Use provided params or defaults
        params = self.DEFAULT_QUERY_PARAMS.copy()
        if query is not None:
            params["query"] = query
        if max_results is not None:
            params["max_results"] = max_results
        if label_ids is not None:
            params["label_ids"] = label_ids
        if include_spam_trash is not None:
            params["include_spam_trash"] = include_spam_trash
        if only_recent is not None:
            params["only_recent"] = only_recent
            
        # Add date filter if only fetching recent emails
        if params["only_recent"]:
            seven_days_ago = (datetime.utcnow() - timedelta(days=7)).strftime('%Y/%m/%d')
            if params["query"]:
                params["query"] += f" after:{seven_days_ago}"
            else:
                params["query"] = f"after:{seven_days_ago}"
        
        # Get messages list
        results = self._execute_service_call(
            lambda: self.service.users().messages().list(
                userId='me', 
                q=params["query"], 
                maxResults=params["max_results"],
                labelIds=params["label_ids"],
                includeSpamTrash=params["include_spam_trash"]
            ).execute(),
            error_message="Error fetching emails"
        )

        if not results:
            return []
            
        messages = results.get('messages', [])
        email_creates = []

        for message in messages:
            # Skip already processed emails
            if message['id'] in self._processed_ids_cache:
                continue
                
            # Get full message details
            msg = self._execute_service_call(
                lambda: self.service.users().messages().get(
                    userId='me', id=message['id'], format='full'
                ).execute(),
                error_message=f"Error getting message {message['id']}"
            )
            
            if not msg:
                continue
                
            try:
                # Use processor to extract all data from the message
                extracted_data = self.processor.extract_message_data(msg, message['id'])
                
                # Parse date
                received_at = datetime.utcnow()
                date_str = extracted_data.get('date')
                if date_str:
                    try:
                        # Try several date formats
                        import email.utils
                        import dateutil.parser
                        
                        try:
                            # RFC 2822 format
                            time_tuple = email.utils.parsedate_tz(date_str)
                            if time_tuple:
                                received_at = datetime.fromtimestamp(email.utils.mktime_tz(time_tuple))
                        except:
                            # Try with dateutil's parser as fallback
                            received_at = dateutil.parser.parse(date_str)
                    except Exception as date_error:
                        logger.warning(f"Error parsing date: {date_error}")
                
                # Create EmailCreate object
                email_create = EmailCreate(
                    email_id=message['id'],
                    sender=extracted_data.get('sender', 'Unknown'),
                    subject=extracted_data.get('subject', 'No Subject'),
                    body=extracted_data.get('body', ''),
                    received_at=received_at,
                    processing_status="pending",
                    attachments=extracted_data.get('attachments', [])
                )
                
                # Add to results
                email_creates.append(email_create)
                
                # Add to processed cache
                self._add_to_processed_cache(message['id'])
                
            except Exception as e:
                logger.error(f"Error processing email {message['id']}: {e}")
                continue
        
        # Save processed IDs cache
        self._save_processed_ids_cache()
        
        return email_creates
    
    def get_attachment_data(self, message_id: str, attachment_id: str) -> Optional[bytes]:
        """
        Get the binary data for an email attachment.
        
        Args:
            message_id: Gmail message ID
            attachment_id: Attachment ID
            
        Returns:
            Binary attachment data or None if error
        """
        attachment = self._execute_service_call(
            lambda: self.service.users().messages().attachments().get(
                userId='me', messageId=message_id, id=attachment_id
            ).execute(),
            error_message=f"Error downloading attachment {attachment_id}"
        )
        
        if attachment:
            data = attachment.get('data', '')
            if data:
                return base64.urlsafe_b64decode(data)
                
        return None
    
    def mark_as_read(self, email_id: str) -> bool:
        """Mark email as read."""
        result = self._execute_service_call(
            lambda: self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute(),
            error_message=f"Error marking email {email_id} as read"
        )
        return result is not None
    
    def mark_as_important(self, email_id: str) -> bool:
        """Mark email as important."""
        result = self._execute_service_call(
            lambda: self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'addLabelIds': ['IMPORTANT']}
            ).execute(),
            error_message=f"Error marking email {email_id} as important"
        )
        return result is not None
    
    def archive_email(self, email_id: str) -> bool:
        """Archive an email (remove INBOX label)."""
        result = self._execute_service_call(
            lambda: self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['INBOX']}
            ).execute(),
            error_message=f"Error archiving email {email_id}"
        )
        return result is not None
    
    def get_labels(self) -> List[Dict[str, Any]]:
        """Get all Gmail labels."""
        result = self._execute_service_call(
            lambda: self.service.users().labels().list(userId='me').execute(),
            error_message="Error getting Gmail labels"
        )
        return result.get('labels', []) if result else []
    
    def apply_label(self, email_id: str, label_name: str) -> bool:
        """Apply a label to an email, creating it if it doesn't exist."""
        # First, check if the label exists
        label_id = self._get_or_create_label(label_name)
        if not label_id:
            return False
            
        # Apply the label
        result = self._execute_service_call(
            lambda: self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'addLabelIds': [label_id]}
            ).execute(),
            error_message=f"Error applying label {label_name} to email {email_id}"
        )
        return result is not None
    
    def _get_or_create_label(self, label_name: str) -> Optional[str]:
        """Get a label ID by name, creating it if it doesn't exist."""
        # Get all labels
        labels = self.get_labels()
        
        # Check if label exists
        for label in labels:
            if label['name'] == label_name:
                return label['id']
        
        # Create label if it doesn't exist
        result = self._execute_service_call(
            lambda: self.service.users().labels().create(
                userId='me',
                body={'name': label_name}
            ).execute(),
            error_message=f"Error creating label {label_name}"
        )
        
        return result['id'] if result else None
    
    def send_email(self, to: str, subject: str, body: str, 
                   attachment_path: Optional[str] = None,
                   cc: Optional[List[str]] = None,
                   bcc: Optional[List[str]] = None) -> Dict[str, str]:
        """Send email with optional attachment and cc/bcc recipients."""
        try:
            # Create message
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            
            # Add CC and BCC if provided
            if cc:
                message['cc'] = ", ".join(cc)
            if bcc:
                message['bcc'] = ", ".join(bcc)
            
            # Add body
            msg = MIMEText(body, 'html')
            message.attach(msg)
            
            # Add attachment if provided
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as f:
                    attachment = MIMEApplication(f.read())
                    attachment_name = os.path.basename(attachment_path)
                    attachment.add_header('Content-Disposition', 'attachment', 
                                         filename=attachment_name)
                    message.attach(attachment)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Send message
            sent_message = self._execute_service_call(
                lambda: self.service.users().messages().send(
                    userId='me', body={'raw': raw_message}
                ).execute(),
                error_message=f"Error sending email to {to}"
            )
            
            if not sent_message:
                return {"message_id": "", "thread_id": ""}
                
            return {
                "message_id": sent_message.get('id', ''),
                "thread_id": sent_message.get('threadId', '')
            }
        except Exception as e:
            logger.error(f"Error creating email to send: {e}")
            return {"message_id": "", "thread_id": ""} 