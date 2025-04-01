"""
Application constants.
"""

from enum import Enum, auto

# File paths
TEMP_DIR = "temp"
LOG_DIR = "logs"
DATA_DIR = "data"
CREDENTIALS_DIR = "credentials"
TEMPLATES_DIR = "templates"

# Template constants
DEFAULT_PROPOSAL_TEMPLATE = "default_proposal.html"
EMAIL_TEMPLATES = {
    "welcome": "welcome_email.html",
    "proposal": "proposal_email.html",
    "reminder": "reminder_email.html",
    "follow_up": "follow_up_email.html"
}

# File extensions
ALLOWED_DOCUMENT_EXTENSIONS = [".pdf", ".docx", ".doc", ".txt", ".rtf"]
ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".bmp"]
ALLOWED_ARCHIVE_EXTENSIONS = [".zip", ".rar", ".7z"]

# API Rate limiting
DEFAULT_RATE_LIMIT = 100  # requests per minute
ADMIN_RATE_LIMIT = 300  # requests per minute

# Processing constants
MAX_ATTACHMENT_SIZE = 25 * 1024 * 1024  # 25 MB
EMAIL_FETCH_LIMIT = 50
TIMEOUT_SECONDS = 30

# User roles
class UserRole(str, Enum):
    ADMIN = "admin"
    STAFF = "staff"
    CLIENT = "client"

# Email processing status
class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Proposal status
class ProposalStatus(str, Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SENT = "sent"

# Delivery status
class DeliveryStatus(str, Enum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"

# Priority levels
class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

# Authentication constants
TOKEN_TYPE = "Bearer"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Error messages
ERROR_MESSAGES = {
    "auth": {
        "invalid_credentials": "Invalid credentials",
        "expired_token": "Token has expired",
        "invalid_token": "Invalid token",
        "insufficient_permissions": "Insufficient permissions"
    },
    "email": {
        "fetch_failed": "Failed to fetch emails",
        "processing_failed": "Failed to process email",
        "send_failed": "Failed to send email"
    },
    "proposal": {
        "not_found": "Proposal not found",
        "creation_failed": "Failed to create proposal",
        "update_failed": "Failed to update proposal"
    },
    "general": {
        "not_found": "Resource not found",
        "validation_error": "Validation error",
        "server_error": "Internal server error"
    }
}
