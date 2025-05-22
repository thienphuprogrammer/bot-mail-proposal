"""
Outlook service implementation that uses the Microsoft Graph API with MSAL.
"""

import os
import base64
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

import msal
import requests

from src.models.email import Email, EmailCreate
from src.services.mail.core.interfaces import BaseMailService
from src.services.mail.processors.outlook_processor import OutlookMailProcessor
from src.core.config import settings
import webbrowser
import re

logger = logging.getLogger(__name__)

class OutlookService(BaseMailService):
    """Outlook service implementation using Microsoft Graph API with MSAL."""
    
    # Microsoft Graph API scopes
    SCOPES = ["Mail.Read", "Mail.Send", "Mail.ReadWrite"]
    
    # Default email query parameters
    DEFAULT_QUERY_PARAMS = {
        "max_results": 100,
        "include_spam_trash": True,
        "folder": "inbox",
        "query": "isRead eq true",
        "only_recent": True  # Only emails from the last 7 days
    }
    
    def __init__(self):
        """Initialize the Outlook service."""
        self.app = self._get_msal_app()
        self.access_token = None
        self.token_expires_at = None
        self.user_id = settings.OUTLOOK_USER_ID
        
        # Create cache directory and initialize processor
        os.makedirs("temp", exist_ok=True)
        self.processor = OutlookMailProcessor(self)
    
    def _get_msal_app(self) -> Optional[msal.ConfidentialClientApplication]:
        """Get the MSAL application instance."""
        try:
            return msal.ConfidentialClientApplication(
                client_id=settings.OUTLOOK_CLIENT_ID,
                client_credential=settings.OUTLOOK_CLIENT_SECRET,
                authority=f"https://login.microsoftonline.com/{settings.OUTLOOK_TENANT_ID}"
            )
        except Exception as e:
            logger.error(f"Failed to build MSAL app: {e}")
            raise ValueError(f"Failed to build MSAL app: {e}")
    
    def _get_access_token(self) -> str:
        """Get a valid access token for Microsoft Graph API."""
        if not self.app:
            raise ValueError("MSAL app not initialized")
            
        # Check if we have a valid token
        if self.access_token and self.token_expires_at and datetime.utcnow() < self.token_expires_at:
            return self.access_token
        
        try:
            # Try refresh token if available
            if os.path.exists(settings.OUTLOOK_TOKEN_PATH):
                with open(settings.OUTLOOK_TOKEN_PATH, 'r') as f:
                    refresh_token = f.read()
                
                result = self.app.acquire_token_by_refresh_token(
                    scopes=self.SCOPES, 
                    refresh_token=refresh_token
                )
                
                if result and "access_token" in result and "error" not in result:
                    self._save_token_result(result)
                    return self.access_token
            
            # Fall back to interactive auth
            return self._interactive_auth()
            
        except Exception as e:
            logger.error(f"Error in token acquisition: {e}")
            return self._interactive_auth()
    
    def _interactive_auth(self) -> str:
        """Handle interactive authentication flow with user prompts."""
        try:
            # Generate auth URL and open browser
            auth_url = self.app.get_authorization_request_url(scopes=self.SCOPES)
            print("\n-------------------------------------------------------")
            print("Please authenticate in your browser:")
            print(auth_url)
            print("-------------------------------------------------------\n")
            
            try:
                webbrowser.open(auth_url)
            except Exception:
                pass
                
            # Get code from user
            auth_code = input("After authenticating, paste the full redirect URL or code here: ")
            
            # Extract code from URL if needed
            if auth_code.startswith("http"):
                code_match = re.search(r"[?&]code=([^&]+)", auth_code)
                if code_match:
                    auth_code = code_match.group(1)
                else:
                    raise ValueError("Could not extract code from provided URL")
            
            # Get token with authorization code
            result = self.app.acquire_token_by_authorization_code(
                scopes=self.SCOPES, 
                code=auth_code
            )
            
            if not result or "error" in result or "access_token" not in result:
                error_desc = result.get("error_description", "Unknown error") if result else "No result"
                raise ValueError(f"Error in token response: {error_desc}")
            
            self._save_token_result(result)
            return self.access_token
            
        except Exception as e:
            logger.error(f"Error in interactive authentication: {e}")
            raise ValueError(f"Authentication failed: {e}")
    
    def _save_token_result(self, result: Dict[str, Any]):
        """Save token information from authentication result."""
        self.access_token = result["access_token"]
        
        # Set expiration to 5 minutes before actual expiration for safety
        self.token_expires_at = datetime.utcnow() + timedelta(
            seconds=result.get("expires_in", 3600) - 300
        )
        
        # Save refresh token if provided
        if "refresh_token" in result:
            try:
                os.makedirs(os.path.dirname(settings.OUTLOOK_TOKEN_PATH), exist_ok=True)
                with open(settings.OUTLOOK_TOKEN_PATH, 'w') as f:
                    f.write(result["refresh_token"])
            except Exception as e:
                logger.warning(f"Error saving refresh token: {e}")
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make an authenticated request to the Microsoft Graph API."""
        if endpoint and ('/None' in endpoint or endpoint.endswith('/')):
            logger.error(f"Invalid endpoint: {endpoint}")
            return None
            
        token = self._get_access_token()
        url = f"https://graph.microsoft.com/v1.0{endpoint}"
        
        try:
            response = requests.request(
                method, 
                url, 
                headers={"Authorization": f"Bearer {token}"}, 
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Graph API request failed: {e}")
            return None
    
    def get_health_status(self) -> Dict[str, Any]:
        """Check if the Outlook service is working properly."""
        if not self.app:
            return {"status": "error", "message": "Service not initialized"}
            
        result = self._make_request('GET', '/me/messages?$top=1')
        
        return {
            "status": "ok" if result else "error",
            "message": "Service is working" if result else "Connection error",
            "timestamp": datetime.utcnow().isoformat()
        }

    def fetch_emails(self, 
                    max_results: int = None, 
                    query: str = None,
                    folder: str = None,
                    include_spam_trash: bool = None,
                    only_recent: bool = None) -> List[EmailCreate]:
        """Fetch emails based on query parameters."""
        # Initialize params with defaults and override with provided values
        params = dict(self.DEFAULT_QUERY_PARAMS)
        if max_results is not None and max_results > 0:
            params["max_results"] = max_results
        if folder:
            params["folder"] = folder  
        if query:
            params["query"] = query
        if include_spam_trash is not None:
            params["include_spam_trash"] = include_spam_trash
        if only_recent is not None:
            params["only_recent"] = only_recent
            
        # Add date filter for recent emails
        if params["only_recent"]:
            seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            date_filter = f"receivedDateTime ge {seven_days_ago}Z"
            params["query"] = f"{params['query'] + ' and ' if params['query'] else ''}{date_filter}"
        
        # Filter out spam/junk if requested
        if not params["include_spam_trash"] and params["folder"].lower() == "inbox":
            not_junk_filter = "categoryId ne 'junkemail'"
            params["query"] = f"{params['query'] + ' and ' if params['query'] else ''}{not_junk_filter}"
        
        # Build query URL
        select_fields = "id,subject,receivedDateTime,from,body,hasAttachments,categories,importance,isRead"
        batch_size = min(100, params['max_results'])
        
        folder_path = f"/mailFolders/{params['folder']}" if params['folder'] else ""
        query_url = (f"/me{folder_path}/messages"
                f"?$top={batch_size}"
                f"&$select={select_fields}"
                f"&$orderby=receivedDateTime desc")
        
        if params["query"]:
            query_url += f"&$filter={params['query']}"
            
        logger.debug(f"Fetching emails with URL: {query_url}")
        
        # Get messages with pagination
        email_creates = []
        total_fetched = 0
        max_to_fetch = params['max_results']
        next_link = query_url
        
        try:
            while next_link and total_fetched < max_to_fetch:
                # Make API request
                if next_link.startswith("https://"):
                    response = requests.get(
                        next_link,
                        headers={"Authorization": f"Bearer {self._get_access_token()}"}
                    )
                    response.raise_for_status()
                    results = response.json()
                else:
                    results = self._make_request('GET', next_link)
                
                if not results or 'value' not in results:
                    break
                    
                messages = results['value']
                if not messages:
                    break
                
                # Process each message with the processor
                for message in messages:
                    # Skip if no ID
                    if not message.get('id'):
                        continue
                        
                    # Check if already processed by processor
                    if self.processor.is_processed(message.get('id')):
                        continue
                        
                    try:
                        # Extract data using processor with interface-compliant method
                        message_data = self.processor.extract_message_data(message, message.get('id'))
                        
                        # Create email object
                        email_create = EmailCreate(
                            email_id=message.get('id'),
                            sender=message_data.get('sender', 'Unknown'),
                            subject=message_data.get('subject', 'No Subject'),
                            body=message_data.get('body', ''),
                            received_at=datetime.fromisoformat(message['receivedDateTime'].replace('Z', '+00:00')),
                            processing_status="pending",
                            attachments=message_data.get('attachments', [])
                        )
                        
                        email_creates.append(email_create)
                        self.processor.mark_as_processed(message.get('id'))
                    except Exception as e:
                        logger.error(f"Error processing message {message.get('id')}: {e}")
                        continue
                
                total_fetched += len(email_creates)
                
                # Check if more pagination needed
                if total_fetched >= max_to_fetch:
                    break
                    
                # Set up next link for pagination
                next_link = results.get('@odata.nextLink')
                if next_link and total_fetched + batch_size > max_to_fetch:
                    remaining = max_to_fetch - total_fetched
                    # Adjust top parameter for next request
                    if next_link.startswith("https://"):
                        separator = "&" if "?" in next_link else "?"
                        next_link = f"{next_link}{separator}$top={remaining}"
                    else:
                        if "$top=" in next_link:
                            next_link = re.sub(r"\$top=\d+", f"$top={remaining}", next_link)
                        else:
                            next_link += f"&$top={remaining}"
            
            logger.info(f"Fetched {len(email_creates)} new emails (requested: {max_to_fetch})")
            return email_creates
            
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []
    
    def get_labels(self) -> List[Dict[str, Any]]:
        """Get all Outlook categories."""
        result = self._make_request('GET', "/me/outlook/masterCategories")
        return result.get('value', []) if result else []
    
    def apply_label(self, email_id: str, label_name: str) -> bool:
        """Apply a category to an email, creating it if it doesn't exist."""
        if not email_id or not label_name:
            return False
            
        # Get or create category
        category_id = self._get_or_create_category(label_name)
        if not category_id:
            return False
            
        # Apply the category
        result = self._make_request(
            'POST', 
            f"/me/messages/{email_id}/categories", 
            json={"categories": [category_id]}
        )
        return result is not None
    
    def _get_or_create_category(self, category_name: str) -> Optional[str]:
        """Get a category ID by name, creating it if it doesn't exist."""
        if not category_name:
            return None
            
        # Check existing categories
        categories = self.get_labels()
        for category in categories:
            if category.get('displayName') == category_name:
                return category.get('id')
        
        # Create new category
        result = self._make_request(
            'POST', 
            "/me/outlook/masterCategories", 
            json={"displayName": category_name}
        )
        
        return result.get('id') if result else None
    
    def send_email(self, to: str, subject: str, body: str, 
                   attachment_paths: Optional[List[str]] = None,
                   cc: Optional[List[str]] = None,
                   bcc: Optional[List[str]] = None,
                   is_html: bool = True,
                   importance: str = "normal",
                   reply_to: Optional[str] = None,
                   template_variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send email with enhanced options.
        
        Args:
            to: Primary recipient email address
            subject: Email subject
            body: Email body content (can be HTML or plain text)
            attachment_paths: List of file paths to attach
            cc: List of CC recipient email addresses
            bcc: List of BCC recipient email addresses
            is_html: Whether the body is HTML (default True)
            importance: Email importance ("low", "normal", "high")
            reply_to: Optional reply-to email address
            template_variables: Variables to substitute in body template if using one
            
        Returns:
            Dictionary with status and message ID information
        """
        if not to:
            return {"success": False, "message": "No recipient specified", "message_id": ""}
            
        try:
            # Apply template variables if provided
            content = body
            if template_variables and isinstance(template_variables, dict):
                for key, value in template_variables.items():
                    placeholder = "{{" + key + "}}"
                    if isinstance(value, list):
                        if is_html:
                            # Convert list to HTML list
                            replacement = "<ul>" + "".join([f"<li>{item}</li>" for item in value]) + "</ul>"
                        else:
                            # Convert list to plain text list
                            replacement = "\n" + "\n".join([f"- {item}" for item in value])
                    else:
                        replacement = str(value) if value is not None else ""
                    
                    content = content.replace(placeholder, replacement)
            
            # Prepare message payload
            message = {
                "subject": subject or "No Subject",
                "body": {
                    "contentType": "html" if is_html else "text",
                    "content": content or ""
                },
                "toRecipients": [{"emailAddress": {"address": to}}],
                "importance": importance if importance in ["low", "normal", "high"] else "normal"
            }
            
            # Add reply-to if provided
            if reply_to:
                message["replyTo"] = [{"emailAddress": {"address": reply_to}}]
            
            # Add CC and BCC if provided
            if cc:
                message["ccRecipients"] = [{"emailAddress": {"address": addr}} for addr in cc if addr]
            if bcc:
                message["bccRecipients"] = [{"emailAddress": {"address": addr}} for addr in bcc if addr]
            
            # Add attachments if provided
            if attachment_paths:
                attachments = []
                for path in attachment_paths:
                    if path and os.path.exists(path):
                        try:
                            with open(path, 'rb') as f:
                                attachment_content = base64.b64encode(f.read()).decode()
                                attachment_name = os.path.basename(path)
                                # Get mime type based on extension
                                content_type = self._get_content_type(path)
                                attachments.append({
                                    "@odata.type": "#microsoft.graph.fileAttachment",
                                    "name": attachment_name,
                                    "contentBytes": attachment_content,
                                    "contentType": content_type
                                })
                        except Exception as e:
                            logger.error(f"Error processing attachment {path}: {e}")
                
                if attachments:
                    message["attachments"] = attachments
            
            # Send message
            result = self._make_request('POST', "/me/sendMail", json={"message": message})
            
            if not result:
                # For Outlook, successful message posting doesn't return content
                # So we check if there was no error in the API call
                logger.info(f"Email sent to {to}")
                return {
                    "success": True,
                    "message": f"Email sent to {to}",
                    "message_id": "",
                    "recipient": to
                }
            else:
                # If we get a result, it's usually an error or additional info
                return {
                    "success": True,
                    "message": f"Email sent to {to}",
                    "message_id": result.get('id', ''),
                    "recipient": to,
                    "data": result
                }
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {
                "success": False, 
                "message": f"Failed to send email: {str(e)}",
                "recipient": to,
                "error": str(e)
            }
    
    def _get_content_type(self, file_path: str) -> str:
        """Determine the MIME content type based on file extension."""
        ext = os.path.splitext(file_path)[1].lower()
        content_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.txt': 'text/plain',
            '.html': 'text/html',
            '.zip': 'application/zip',
            '.csv': 'text/csv'
        }
        return content_types.get(ext, 'application/octet-stream')
    
    def get_attachment_data(self, message_id: str, attachment_id: str) -> Optional[bytes]:
        """Get the binary data for an email attachment."""
        if not message_id or not attachment_id:
            return None
                
        attachment = self._make_request(
            'GET', 
            f"/users/{self.user_id}/messages/{message_id}/attachments/{attachment_id}"
        )
        
        if attachment and 'contentBytes' in attachment:
            return base64.b64decode(attachment['contentBytes'])
        
        return None
    
    def mark_as_read(self, email_id: str) -> bool:
        """Mark email as read."""
        if not email_id:
            return False
            
        result = self._make_request(
            'PATCH', 
            f"/me/messages/{email_id}", 
            json={"isRead": True}
        )
        return result is not None
    
    def mark_as_important(self, email_id: str) -> bool:
        """Mark email as important."""
        if not email_id:
            return False
            
        result = self._make_request(
            'PATCH', 
            f"/me/messages/{email_id}", 
            json={"importance": "high"}
        )
        return result is not None
    
    def archive_email(self, email_id: str) -> bool:
        """Archive an email (move to Archive folder)."""
        if not email_id:
            return False
            
        result = self._make_request(
            'POST', 
            f"/me/messages/{email_id}/move", 
            json={"destinationId": "archive"}
        )
        return result is not None 