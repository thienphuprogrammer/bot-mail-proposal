"""Email processing and content extraction implementations."""

from src.services.mail.processors.gmail_processor import GmailMailProcessor
from src.services.mail.processors.outlook_processor import OutlookMailProcessor

__all__ = [
    "GmailMailProcessor",
    "OutlookMailProcessor",
] 