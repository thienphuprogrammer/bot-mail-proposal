"""
Factory for creating mail service components with proper dependency injection.
"""

from typing import Dict, Any, Optional, Type

from src.services.mail.core.interfaces import BaseMailService, MailProcessor, MailFilter
from src.services.mail.core.mail_facade import MailServiceFacade
from src.services.mail.providers.gmail_service import GmailService
from src.services.mail.providers.outlook_service import OutlookService
from src.services.mail.processors.gmail_processor import GmailMailProcessor
from src.services.mail.processors.outlook_processor import OutlookMailProcessor
from src.services.mail.filters.mail_filter import MailFilterService
from src.repositories.email_repository import EmailRepository

class MailServiceFactory:
    """Factory for creating mail service components."""
    
    @staticmethod
    def create_gmail_service() -> GmailService:
        """Create and configure a Gmail service."""
        return GmailService()
    
    @staticmethod
    def create_outlook_service() -> OutlookService:
        """Create and configure an Outlook service."""
        return OutlookService()
    
    @staticmethod
    def create_mail_processor(mail_service: BaseMailService) -> MailProcessor:
        """Create and configure a mail processor."""
        if isinstance(mail_service, GmailService):
            return GmailMailProcessor(mail_service)
        elif isinstance(mail_service, OutlookService):
            return OutlookMailProcessor(mail_service)
        else:
            raise ValueError(f"Unsupported mail service type: {type(mail_service)}")
    
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
        email_repository: Optional[EmailRepository] = None,
        provider: str = "gmail"
    ) -> MailServiceFacade:
        """
        Create a complete mail service facade with all dependencies.
        
        Args:
            mail_service: Optional mail service instance
            mail_processor: Optional mail processor instance
            mail_filter: Optional mail filter instance
            email_repository: Optional email repository instance
            provider: Email provider to use ("gmail" or "outlook")
            
        Returns:
            MailServiceFacade instance with all dependencies configured
        """
        # Create components if not provided
        if mail_service is None:
            if provider.lower() == "gmail":
                mail_service = MailServiceFactory.create_gmail_service()
            elif provider.lower() == "outlook":
                mail_service = MailServiceFactory.create_outlook_service()
            else:
                raise ValueError(f"Unsupported email provider: {provider}")
            
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
        return MailServiceFactory.create_mail_facade(provider="gmail")
    
    @staticmethod
    def create_default_outlook_facade() -> MailServiceFacade:
        """Create a default Outlook-based mail service facade."""
        return MailServiceFactory.create_mail_facade(provider="outlook") 