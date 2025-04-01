"""
Factory for creating mail service components with proper dependency injection.
"""

from typing import Dict, Any, Optional, Type

from services.mail.core.interfaces import BaseMailService, MailProcessor, MailFilter
from services.mail.core.mail_facade import MailServiceFacade
from services.mail.providers.gmail_service import GmailService
from services.mail.processors.gmail_processor import GmailMailProcessor
from services.mail.filters.mail_filter import MailFilterService
from repositories.email_repository import EmailRepository

class MailServiceFactory:
    """Factory for creating mail service components."""
    
    @staticmethod
    def create_gmail_service() -> GmailService:
        """Create and configure a Gmail service."""
        return GmailService()
    
    @staticmethod
    def create_mail_processor(mail_service: BaseMailService) -> GmailMailProcessor:
        """Create and configure a mail processor."""
        return GmailMailProcessor(mail_service)
    
    @staticmethod
    def create_mail_filter() -> MailFilterService:
        """Create and configure a mail filter."""
        return MailFilterService()
    
    @staticmethod
    def create_email_repository() -> EmailRepository:
        """Create and configure an email repository."""
        return EmailRepository()
    
    @staticmethod
    def create_mail_facade(
        mail_service: Optional[BaseMailService] = None,
        mail_processor: Optional[MailProcessor] = None,
        mail_filter: Optional[MailFilter] = None,
        email_repository: Optional[EmailRepository] = None
    ) -> MailServiceFacade:
        """
        Create a complete mail service facade with all dependencies.
        
        If any component is not provided, it will be created automatically.
        """
        # Create components if not provided
        if mail_service is None:
            mail_service = MailServiceFactory.create_gmail_service()
            
        if mail_processor is None:
            mail_processor = MailServiceFactory.create_mail_processor(mail_service)
            
        if mail_filter is None:
            mail_filter = MailServiceFactory.create_mail_filter()
        
        if email_repository is None:
            email_repository = MailServiceFactory.create_email_repository()
        
        # Create and return the facade
        return MailServiceFacade(
            mail_service=mail_service,
            mail_processor=mail_processor,
            mail_filter=mail_filter,
            email_repository=email_repository
        )
    
    @staticmethod
    def create_default_gmail_facade() -> MailServiceFacade:
        """Create a default Gmail-based mail service facade."""
        return MailServiceFactory.create_mail_facade() 