"""
Base Mail Service Interfaces
===========================

This module defines the core interfaces that all mail service implementations must follow.
The design uses the Interface Segregation Principle to separate different concerns:

1. BaseMailService: Core email provider operations
2. MailProcessor: Email content extraction and processing
3. MailFilter: Email categorization and filtering

Each implementation should respect these interfaces to ensure consistent behavior
across different mail providers.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Tuple

class BaseMailService(ABC):
    """Base interface for all email service providers."""
    
    @abstractmethod
    def fetch_emails(self, max_results: int = 10, query: str = "") -> List[Any]:
        """
        Fetch emails from the email provider.
        
        Args:
            max_results: Maximum number of emails to fetch
            query: Search query to filter emails
            
        Returns:
            List of email objects
        """
        pass
    
    @abstractmethod
    def mark_as_read(self, email_id: str) -> bool:
        """
        Mark an email as read.
        
        Args:
            email_id: ID of the email to mark as read
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def send_email(self, to: str, subject: str, body: str, 
                  attachment_path: Optional[str] = None,
                  cc: Optional[List[str]] = None,
                  bcc: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Send an email.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            attachment_path: Optional path to an attachment file
            cc: Optional list of CC recipients
            bcc: Optional list of BCC recipients
            
        Returns:
            Dictionary with message_id and thread_id
        """
        pass
    
    @abstractmethod
    def get_labels(self) -> List[Dict[str, Any]]:
        """
        Get all available email labels/folders.
        
        Returns:
            List of label dictionaries with id and name
        """
        pass
    
    @abstractmethod
    def apply_label(self, email_id: str, label_name: str) -> bool:
        """
        Apply a label to an email.
        
        Args:
            email_id: ID of the email to label
            label_name: Name of the label to apply
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def archive_email(self, email_id: str) -> bool:
        """
        Move an email to archive.
        
        Args:
            email_id: ID of the email to archive
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def mark_as_important(self, email_id: str) -> bool:
        """
        Mark an email as important.
        
        Args:
            email_id: ID of the email to mark
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """
        Check the health status of the email service.
        
        Returns:
            Dictionary with status information
        """
        pass
    
    @abstractmethod
    def get_attachment_data(self, message_id: str, attachment_id: str) -> Optional[bytes]:
        """
        Get binary data for an email attachment.
        
        Args:
            message_id: ID of the email containing the attachment
            attachment_id: ID of the attachment to retrieve
            
        Returns:
            Binary attachment data or None if not found
        """
        pass


class MailProcessor(ABC):
    """Interface for mail content processing and extraction."""
    
    @abstractmethod
    def extract_body(self, payload: Dict[str, Any]) -> str:
        """
        Extract the body of an email from the payload.
        
        Args:
            payload: Email message payload
            
        Returns:
            Extracted email body text
        """
        pass
    
    @abstractmethod
    def get_email_details(self, email_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific email.
        
        Args:
            email_id: ID of the email to retrieve
            
        Returns:
            Dictionary with email details
        """
        pass
    
    @abstractmethod
    def extract_message_data(self, message: Dict[str, Any], message_id: str) -> Dict[str, Any]:
        """
        Extract all relevant data from a raw message object.
        
        Args:
            message: Raw message data
            message_id: ID of the message
            
        Returns:
            Dictionary with extracted message data
        """
        pass
    
    @abstractmethod
    def extract_metadata(self, email: Any) -> Dict[str, Any]:
        """
        Extract metadata from an email for analysis.
        
        Args:
            email: Email object to analyze
            
        Returns:
            Dictionary with metadata about the email
        """
        pass


class MailFilter(ABC):
    """Interface for mail filtering and categorization."""
    
    @abstractmethod
    def is_spam(self, email: Any) -> Tuple[bool, Dict[str, Any]]:
        """
        Determine if an email is spam.
        
        Args:
            email: Email object to check
            
        Returns:
            Tuple of (is_spam, details) where details contains the reasons
        """
        pass
    
    @abstractmethod
    def detect_email_intent(self, email: Any) -> Dict[str, Any]:
        """
        Detect the intent of an email.
        
        Args:
            email: Email object to analyze
            
        Returns:
            Dictionary with intent classification results
        """
        pass
    
    @abstractmethod
    def filter_emails(self, emails: List[Any]) -> Dict[str, List[Any]]:
        """
        Filter emails into categories.
        
        Args:
            emails: List of email objects to categorize
            
        Returns:
            Dictionary with categories as keys and lists of emails as values
        """
        pass 