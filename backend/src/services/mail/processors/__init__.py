"""Email processing and content extraction implementations."""

from services.mail.processors.gmail_processor import GmailMailProcessor
from services.mail.processors.outlook_processor import OutlookMailProcessor

__all__ = [
    "GmailMailProcessor",
    "OutlookMailProcessor",
] 