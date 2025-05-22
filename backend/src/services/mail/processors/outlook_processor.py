"""
Mail processor implementation for handling Outlook email content extraction.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from pathlib import Path

from src.services.mail.core.interfaces import MailProcessor, BaseMailService
from src.models.email import Email, EmailCreate
from bs4 import BeautifulSoup
import re
import html
import unicodedata

logger = logging.getLogger(__name__)

class OutlookMailProcessor(MailProcessor):
    """Outlook-specific mail processor implementation."""
    
    def __init__(self, mail_service: BaseMailService):
        """Initialize with a mail service instance."""
        self.mail_service = mail_service
        
        # Create cache directory and initialize processed IDs tracking
        os.makedirs("temp/attachments", exist_ok=True)
        self._processed_ids_cache = set()
        self._cache_file = os.path.join("temp", "processed_outlook_ids.json")
        self._load_processed_ids_cache()

    def _load_processed_ids_cache(self):
        """Load the cache of processed email IDs."""
        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, 'r') as f:
                    self._processed_ids_cache = set(json.load(f))
                logger.debug(f"Loaded {len(self._processed_ids_cache)} processed email IDs from cache")
            else:
                self._processed_ids_cache = set()
        except Exception as e:
            logger.error(f"Error loading processed IDs cache: {e}")
            self._processed_ids_cache = set()
    
    def _save_processed_ids_cache(self):
        """Save the cache of processed email IDs."""
        try:
            with open(self._cache_file, 'w') as f:
                json.dump(list(self._processed_ids_cache), f)
        except Exception as e:
            logger.error(f"Error saving processed IDs cache: {e}")
    
    def is_processed(self, message_id: str) -> bool:
        """Check if a message has already been processed."""
        return message_id in self._processed_ids_cache if message_id else False
    
    def mark_as_processed(self, message_id: str):
        """Mark a message as processed and save periodically."""
        if not message_id or message_id in self._processed_ids_cache:
            return
            
        self._processed_ids_cache.add(message_id)
        # Periodically save the cache (not every time to reduce disk I/O)
        if len(self._processed_ids_cache) % 10 == 0:
            self._save_processed_ids_cache()

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean email content by removing HTML tags and normalizing whitespace."""
        if not text:
            return ""
            
        # Normalize line endings and decode HTML 
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        text = html.unescape(text)
        
        # Remove HTML tags and normalize whitespace
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove control characters except tab and newline
        text = ''.join(ch for ch in text if unicodedata.category(ch)[0] != 'C' or ch in '\t\n')
        
        return text.strip()

    def extract_body(self, payload: Dict[str, Any]) -> str:
        """
        Extract the body of an email from the payload.
        
        Args:
            payload: Email message payload
            
        Returns:
            Extracted email body text
        """
        try:
            # Handle payload structure for Outlook API
            body_data = payload.get('body', payload)  # Handle both full message and body-only payloads
            content = body_data.get('content', '')
            content_type = body_data.get('contentType', 'text')
            
            if content_type == 'html':
                soup = BeautifulSoup(content, 'html.parser')
                return self.clean_text(soup.get_text())
            else:
                return self.clean_text(content)
        except Exception as e:
            logger.error(f"Error extracting email body: {e}")
            return ""

    def get_email_details(self, email_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific email.
        
        Args:
            email_id: ID of the email to retrieve
            
        Returns:
            Dictionary with email details
        """
        try:
            # Fetch full message details
            message = self.mail_service._make_request(
                "GET",
                f"/me/messages/{email_id}?$expand=attachments"
            )
            
            if not message:
                return {}
                
            # Extract data from message
            result = {
                'id': message.get('id', ''),
                'subject': message.get('subject', 'No Subject'),
                'sender': message.get('from', {}).get('emailAddress', {}).get('address', 'Unknown'),
                'recipients': [r.get('emailAddress', {}).get('address') for r in message.get('toRecipients', [])],
                'cc': [r.get('emailAddress', {}).get('address') for r in message.get('ccRecipients', [])],
                'bcc': [r.get('emailAddress', {}).get('address') for r in message.get('bccRecipients', [])],
                'received_at': message.get('receivedDateTime'),
                'sent_at': message.get('sentDateTime'),
                'is_read': message.get('isRead', False),
                'is_draft': message.get('isDraft', False),
                'importance': message.get('importance', 'normal'),
                'categories': message.get('categories', []),
                'has_attachments': message.get('hasAttachments', False),
                'body': self.extract_body(message),
                'attachments': self._process_attachments(message.get('attachments', []))
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting email details: {e}")
            return {}

    def extract_message_data(self, message: Dict[str, Any], message_id: str) -> Dict[str, Any]:
        """
        Extract all relevant data from a raw message object.
        
        Args:
            message: Raw message data
            message_id: ID of the message
            
        Returns:
            Dictionary with extracted message data
        """
        try:
            # For messages that don't have all the data, fetch additional details
            if not message.get('body') or (message.get('hasAttachments') and 'attachments' not in message):
                details = self.get_email_details(message_id)
                
                # If we got detailed data, use it
                if details:
                    return {
                        'id': message_id,
                        'subject': details.get('subject', 'No Subject'),
                        'sender': details.get('sender', 'Unknown'),
                        'body': details.get('body', ''),
                        'received_at': details.get('received_at'),
                        'attachments': details.get('attachments', []),
                        'categories': details.get('categories', []),
                        'importance': details.get('importance', 'normal'),
                        'is_read': details.get('is_read', False)
                    }
            
            # Extract basic message data from what we have
            result = {
                'id': message_id,
                'subject': message.get('subject', 'No Subject'),
                'sender': message.get('from', {}).get('emailAddress', {}).get('address', 'Unknown'),
                'received_at': message.get('receivedDateTime'),
                'has_attachments': message.get('hasAttachments', False),
                'importance': message.get('importance', 'normal'),
                'categories': message.get('categories', []),
                'is_read': message.get('isRead', False),
                'body': self.extract_body(message) if 'body' in message else '',
                'attachments': self._process_attachments(message.get('attachments', []))
            }
                
            return result
        except Exception as e:
            logger.error(f"Error extracting message data: {e}")
            return {
                'id': message_id,
                'subject': message.get('subject', 'Error Processing Email'),
                'sender': 'unknown',
                'body': '',
                'attachments': []
            }

    def _process_attachments(self, attachments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process attachment information from a message."""
        result = []
        
        try:
            for attachment in attachments:
                if attachment.get('@odata.type') == '#microsoft.graph.fileAttachment':
                    result.append({
                        'id': attachment.get('id'),
                        'name': attachment.get('name'),
                        'content_type': attachment.get('contentType'),
                        'size': attachment.get('size'),
                        'is_inline': attachment.get('isInline', False)
                    })
        except Exception as e:
            logger.error(f"Error processing attachments: {e}")
            
        return result
            
    def process_message_batch(self, messages: List[Dict[str, Any]]) -> List[EmailCreate]:
        """Process a batch of messages and create EmailCreate objects."""
        email_creates = []
        
        for message in messages:
            # Skip messages with no ID or already processed
            message_id = message.get('id')
            if not message_id or self.is_processed(message_id):
                continue
                
            try:
                # Extract all data from the message
                extracted_data = self.extract_message_data(message, message_id)
                
                email_create = EmailCreate(
                    email_id=message_id,
                    sender=extracted_data.get('sender', 'Unknown'),
                    subject=extracted_data.get('subject', 'No Subject'),
                    body=extracted_data.get('body', ''),
                    received_at=datetime.fromisoformat(message['receivedDateTime'].replace('Z', '+00:00')),
                    processing_status="pending",
                    attachments=extracted_data.get('attachments', [])
                )
                
                email_creates.append(email_create)
                self.mark_as_processed(message_id)
                
            except Exception as e:
                logger.error(f"Error processing email {message_id}: {e}")
                continue
        
        # Save processed IDs cache if we processed any messages
        if email_creates:
            self._save_processed_ids_cache()
            
        return email_creates
            
    def extract_metadata(self, email: Any) -> Dict[str, Any]:
        """
        Extract metadata from an email for analysis.
        
        Args:
            email: Email object to analyze
            
        Returns:
            Dictionary with metadata about the email
        """
        try:
            return {
                'id': email.id,
                'subject': email.subject,
                'sender': email.sender,
                'received_at': email.received_at.isoformat() if email.received_at else None,
                'processing_status': email.processing_status,
                'has_attachments': bool(email.attachments),
                'attachment_count': len(email.attachments) if email.attachments else 0,
                'categories': email.categories if hasattr(email, 'categories') else [],
                'importance': email.importance if hasattr(email, 'importance') else 'normal'
            }
            
        except Exception as e:
            logger.error(f"Error extracting email metadata: {e}")
            return {} 