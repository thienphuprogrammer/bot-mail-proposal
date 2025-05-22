"""
Mail processor implementation for handling email content extraction.
"""

import os
import base64
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path

from src.services.mail.core.interfaces import MailProcessor, BaseMailService
from src.models.email import Email
from bs4 import BeautifulSoup
import re
import html
import unicodedata
from email.utils import parsedate_to_datetime

logger = logging.getLogger(__name__)

class GmailMailProcessor(MailProcessor):
    """Gmail-specific mail processor implementation."""
    
    def __init__(self, mail_service: BaseMailService):
        """Initialize with a mail service instance."""
        self.mail_service = mail_service
        self.attachment_dir = Path("temp/attachments")
        self.attachment_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def clean_context(text: str) -> str:
        """
        Clean email content by removing special characters, normalizing whitespace,
        and ensuring proper formatting.
        
        Args:
            text: Raw email content to clean.
        
        Returns:
            Cleaned and formatted email content.
        """
        if not text:
            return ""
            
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Remove any remaining HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Normalize whitespace
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove control characters except tab and newline
        text = ''.join(ch for ch in text if unicodedata.category(ch)[0] != 'C' or ch in '\t\n')
        
        return text.strip()

    def extract_body(self, payload: Dict[str, Any]) -> str:
        """
        Extract the plain text content of an email body from its payload.

        Args:
            payload: The Gmail API payload containing email parts.

        Returns:
            The email body as plain text, with HTML tags stripped if applicable.
        """
        try:
            # Try to extract HTML content first
            html_content = self._extract_mime_part(payload, 'text/html')
            if html_content:
                soup = BeautifulSoup(html_content, 'html.parser')
                return self.clean_context(soup.get_text())
            
            # Fallback to plain text
            plain_content = self._extract_mime_part(payload, 'text/plain')
            if plain_content:
                return self.clean_context(plain_content)
            
            # Last resort: try to get content from payload body
            body = payload.get('body', {})
            data = body.get('data', '')
            if data:
                content_bytes = base64.urlsafe_b64decode(data)
                mime_type = payload.get('mimeType', '')
                if mime_type.startswith('text/html'):
                    html_content = content_bytes.decode('utf-8', errors='replace')
                    soup = BeautifulSoup(html_content, 'html.parser')
                    return self.clean_context(soup.get_text())
                return self.clean_context(content_bytes.decode('utf-8', errors='replace'))
            
            logger.warning("No body content found in email payload")
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting email body: {e}")
            return "Error extracting body"
    
    def _extract_mime_part(self, part: Dict[str, Any], mime_type: str) -> Optional[str]:
        """
        Recursively extract content of specified MIME type from message parts.

        Args:
            part: A dictionary representing a message part from the Gmail API.
            mime_type: The MIME type to extract (e.g., 'text/html', 'text/plain').

        Returns:
            The decoded content as a string, or None if not found.
        """
        if part.get('mimeType') == mime_type:
            body_data = part.get('body', {}).get('data')
            if body_data:
                try:
                    content_bytes = base64.urlsafe_b64decode(body_data)
                    charset = self._get_charset(part)
                    return content_bytes.decode(charset or 'utf-8', errors='replace')
                except Exception as e:
                    logger.error(f"Error decoding MIME part: {e}")
                    return None
                
        # Check nested parts
        if 'parts' in part:
            for subpart in part['parts']:
                content = self._extract_mime_part(subpart, mime_type)
                if content:
                    return content
                    
        return None
    
    def _get_charset(self, part: Dict[str, Any]) -> Optional[str]:
        """Extract charset from part headers."""
        for header in part.get('headers', []):
            if header['name'].lower() == 'content-type':
                content_type = header['value']
                if 'charset=' in content_type:
                    return content_type.split('charset=')[1].split(';')[0].strip()
        return None
    
    def get_attachments(self, message: Dict[str, Any], message_id: str) -> List[str]:
        """
        Download attachments from the email and return their paths.
        
        Args:
            message: The Gmail message object
            message_id: The Gmail message ID
            
        Returns:
            List of paths to downloaded attachments
        """
        attachments = []
        
        try:
            def process_parts(parts: List[Dict[str, Any]], part_path: str = "") -> None:
                for i, part in enumerate(parts):
                    current_path = f"{part_path}.{i}" if part_path else str(i)
                    
                    # Check for attachment
                    filename = part.get('filename')
                    if filename and filename.strip():
                        attachment_id = part.get('body', {}).get('attachmentId')
                        if attachment_id:
                            try:
                                attachment_data = self.mail_service.get_attachment_data(message_id, attachment_id)
                                if attachment_data:
                                    safe_filename = os.path.basename(filename)
                                    file_path = self.attachment_dir / f"{message_id}_{safe_filename}"
                                    
                                    with open(file_path, 'wb') as f:
                                        f.write(attachment_data)
                                    
                                    attachments.append(str(file_path))
                            except Exception as e:
                                logger.error(f"Error downloading attachment {filename}: {e}")
                    
                    # Process nested parts
                    if 'parts' in part:
                        process_parts(part['parts'], current_path)
            
            if 'parts' in message['payload']:
                process_parts(message['payload']['parts'])
                
        except Exception as e:
            logger.error(f"Error processing attachments: {e}")
            
        return attachments
    
    def get_email_details(self, email_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific email.
        
        Args:
            email_id: The email ID to fetch details for
            
        Returns:
            Dictionary containing email details
        """
        try:
            query = f"rfc822msgid:{email_id}"
            emails = self.mail_service.fetch_emails(query=query, max_results=1)
            
            if not emails:
                logger.warning(f"Email not found with ID: {email_id}")
                return self._create_empty_email_details()
                
            email = emails[0]
            
            # Mark as read
            self.mail_service.mark_as_read(email.email_id)
            
            return {
                'email_id': email.id,
                'email_id': email.email_id,
                'subject': email.subject,
                'sender': email.sender,
                'receiver': '',  # TODO: Add to EmailCreate model
                'snippet': self._create_snippet(email.body),
                'has_attachment': bool(email.attachments),
                'date': email.received_at.isoformat() if email.received_at else '',
                'star': False,  # TODO: Add to EmailCreate model
                'label': '',  # TODO: Add to EmailCreate model
                'body': email.body,
                'attachments': email.attachments
            }
        except Exception as e:
            logger.error(f"Error getting email details: {e}")
            return self._create_empty_email_details()
    
    def _create_empty_email_details(self) -> Dict[str, Any]:
        """Create empty email details dictionary."""
        return {
            'subject': 'Email not found',
            'sender': '',
            'receiver': '',
            'snippet': '',
            'has_attachment': False,
            'date': '',
            'star': False,
            'label': '',
            'body': ''
        }
    
    def _create_snippet(self, body: str, max_length: int = 100) -> str:
        """Create a snippet from email body."""
        if not body:
            return ""
        return body[:max_length] + '...' if len(body) > max_length else body
    
    def extract_metadata(self, email: Email) -> Dict[str, Any]:
        """
        Extract metadata from an email for analysis.
        
        Args:
            email: The email to extract metadata from
            
        Returns:
            Dictionary of metadata including sender info, keywords, etc.
        """
        return {
            'sender_info': self._parse_sender_info(email.sender),
            'subject_keywords': self._extract_keywords(email.subject),
            'content_length': len(email.body),
            'has_attachments': bool(email.attachments),
            'attachment_count': len(email.attachments),
            'attachment_types': self._get_attachment_types(email.attachments)
        }
    
    def extract_message_data(self, message: Dict[str, Any], message_id: str) -> Dict[str, Any]:
        """
        Extract all relevant data from a raw Gmail message.
        
        Args:
            message: Raw Gmail message object
            message_id: Gmail message ID
            
        Returns:
            Dictionary with extracted email data
        """
        try:
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
            to = next((h['value'] for h in headers if h['name'].lower() == 'to'), '')
            date_str = next((h['value'] for h in headers if h['name'].lower() == 'date'), None)
            
            # Parse date if available
            date = parsedate_to_datetime(date_str) if date_str else None
            
            return {
                'message_id': message_id,
                'subject': subject,
                'sender': sender,
                'receiver': to,
                'date': date.isoformat() if date else None,
                'body': self.extract_body(message['payload']),
                'snippet': message.get('snippet', ''),
                'label_ids': message.get('labelIds', []),
                'has_attachment': bool(message.get('payload', {}).get('parts')),
                'attachments': self.get_attachments(message, message_id)
            }
        except Exception as e:
            logger.error(f"Error extracting message data: {e}")
            return {
                'message_id': message_id,
                'subject': 'Error extracting data',
                'body': f"Error: {str(e)}",
                'sender': '',
                'date': '',
                'attachments': []
            }
    
    def _parse_sender_info(self, sender: str) -> Dict[str, str]:
        """
        Parse sender information into name and email parts.
        
        Args:
            sender: Raw sender string
            
        Returns:
            Dictionary with parsed sender information
        """
        try:
            if '<' in sender and '>' in sender:
                name = sender.split('<')[0].strip()
                email = sender.split('<')[1].split('>')[0].strip()
            else:
                name = ''
                email = sender.strip()
            
            domain = email.split('@')[-1] if '@' in email else ''
            
            return {
                'name': name,
                'email': email,
                'domain': domain
            }
        except Exception as e:
            logger.error(f"Error parsing sender info: {e}")
            return {
                'name': '',
                'email': sender,
                'domain': ''
            }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract important keywords from text.
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            List of extracted keywords
        """
        if not text:
            return []
            
        # Remove punctuation and split into words
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'is', 'in', 'to', 'for', 'of', 'with', 'on', 'at'}
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords[:10]  # Return up to 10 keywords
    
    def _get_attachment_types(self, attachments: List[str]) -> Dict[str, int]:
        """
        Get count of each attachment type.
        
        Args:
            attachments: List of attachment paths
            
        Returns:
            Dictionary with attachment type counts
        """
        type_counts = {}
        
        for attachment_path in attachments:
            try:
                extension = Path(attachment_path).suffix.lower().lstrip('.')
                if extension:
                    type_counts[extension] = type_counts.get(extension, 0) + 1
                else:
                    type_counts['unknown'] = type_counts.get('unknown', 0) + 1
            except Exception as e:
                logger.error(f"Error processing attachment type: {e}")
                type_counts['unknown'] = type_counts.get('unknown', 0) + 1
                
        return type_counts 