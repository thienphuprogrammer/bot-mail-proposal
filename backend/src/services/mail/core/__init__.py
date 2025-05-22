"""Core mail service interfaces and base implementations."""

from src.services.mail.core.interfaces import BaseMailService, MailProcessor, MailFilter
from src.services.mail.core.mail_facade import MailServiceFacade
from src.services.mail.core.mail_factory import MailServiceFactory

__all__ = [
    "BaseMailService",
    "MailProcessor",
    "MailFilter",
    "MailServiceFacade",
    "MailServiceFactory",
] 