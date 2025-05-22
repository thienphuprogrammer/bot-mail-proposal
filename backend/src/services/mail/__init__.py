"""
Mail Service Package
===================

A comprehensive mail processing system that handles email operations including 
fetching, filtering, and processing. The architecture follows a clean separation 
of concerns with dependency injection for better testability.

Directory Structure:
- core/: Core interfaces and service orchestration
- providers/: Email provider implementations (Gmail, Outlook, etc.)
- processors/: Email content extraction and processing
- filters/: Email categorization and filtering

Usage Example:
    ```python
    from src.services.mail import create_mail_service
    
    # Get a configured email service
    mail_service = create_mail_service()
    
    # Fetch and process emails
    results = await mail_service.fetch_and_process_emails(max_results=20)
    ```
"""

# Export core interfaces and classes
from src.services.mail.core import (
    BaseMailService,
    MailProcessor,
    MailFilter,
    MailServiceFacade,
    MailServiceFactory,
)

# Export provider implementations
from src.services.mail.providers import GmailService, OutlookService

# Export processor implementations
from src.services.mail.processors import GmailMailProcessor, OutlookMailProcessor

# Export filter implementations
from src.services.mail.filters import MailFilterService

__all__ = [
    # Core interfaces
    "BaseMailService",
    "MailProcessor", 
    "MailFilter",
    "MailServiceFacade",
    "MailServiceFactory",
    
    # Providers
    "GmailService",
    "OutlookService",
    
    # Processors
    "GmailMailProcessor",
    "OutlookMailProcessor",
    
    # Filters
    "MailFilterService"
] 