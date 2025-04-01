"""
Validation utilities for input validation and sanitization.
"""

import re
import html
from typing import Any, Dict, List, Optional, Pattern, Set, Union
from email.utils import parseaddr
import json
from datetime import datetime
import uuid

# Commonly used regex patterns
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
URL_PATTERN = re.compile(r'^(https?:\/\/)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$')
PHONE_PATTERN = re.compile(r'^\+?[0-9]{10,15}$')
UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')


def is_valid_email(email: str) -> bool:
    """
    Validate an email address.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not email or len(email) > 320:  # RFC 3696
        return False
        
    # Use both regex and parseaddr for comprehensive validation
    if not EMAIL_PATTERN.match(email):
        return False
        
    # Check with parseaddr
    name, addr = parseaddr(email)
    if not addr or addr != email:
        return False
        
    return True


def is_valid_url(url: str) -> bool:
    """
    Validate a URL.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not url or len(url) > 2048:  # Common URL length limit
        return False
        
    return bool(URL_PATTERN.match(url))


def is_valid_phone(phone: str) -> bool:
    """
    Validate a phone number.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not phone:
        return False
        
    # Remove common separators for validation
    clean_phone = re.sub(r'[\s\-\(\)\.]+', '', phone)
    
    return bool(PHONE_PATTERN.match(clean_phone))


def is_valid_uuid(uuid_str: str) -> bool:
    """
    Validate a UUID string.
    
    Args:
        uuid_str: UUID string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not uuid_str:
        return False
        
    try:
        # Try to parse with uuid module
        uuid_obj = uuid.UUID(uuid_str)
        return str(uuid_obj) == uuid_str
    except ValueError:
        return False


def sanitize_html(html_content: str) -> str:
    """
    Sanitize HTML content by escaping special characters.
    
    Args:
        html_content: HTML content to sanitize
        
    Returns:
        Sanitized HTML
    """
    return html.escape(html_content)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing unsafe characters.
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename
    """
    # Remove unsafe characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Limit length
    if len(sanitized) > 255:
        base, ext = os.path.splitext(sanitized)
        sanitized = f"{base[:255-len(ext)]}{ext}"
        
    return sanitized


def is_valid_json(json_str: str) -> bool:
    """
    Check if a string is valid JSON.
    
    Args:
        json_str: JSON string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        json.loads(json_str)
        return True
    except (ValueError, TypeError):
        return False


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """
    Validate that all required fields are present in a dictionary.
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        
    Returns:
        List of missing field names
    """
    return [field for field in required_fields if field not in data or data[field] is None]


def validate_field_type(value: Any, expected_type: Any) -> bool:
    """
    Validate that a value is of the expected type.
    
    Args:
        value: Value to validate
        expected_type: Expected type
        
    Returns:
        True if valid, False otherwise
    """
    # Handle None values
    if value is None:
        return expected_type is type(None)
        
    # Handle Union types (Python 3.8+)
    if hasattr(expected_type, "__origin__") and expected_type.__origin__ is Union:
        return any(validate_field_type(value, t) for t in expected_type.__args__)
        
    # Handle Lists
    if hasattr(expected_type, "__origin__") and expected_type.__origin__ is list:
        if not isinstance(value, list):
            return False
        # If we have a type argument, check each item
        if hasattr(expected_type, "__args__") and expected_type.__args__:
            item_type = expected_type.__args__[0]
            return all(validate_field_type(item, item_type) for item in value)
        return True
        
    # Handle Dicts
    if hasattr(expected_type, "__origin__") and expected_type.__origin__ is dict:
        if not isinstance(value, dict):
            return False
        # If we have key and value type arguments, check them
        if hasattr(expected_type, "__args__") and len(expected_type.__args__) == 2:
            key_type, val_type = expected_type.__args__
            return all(
                validate_field_type(k, key_type) and validate_field_type(v, val_type)
                for k, v in value.items()
            )
        return True
        
    # Handle Sets
    if hasattr(expected_type, "__origin__") and expected_type.__origin__ is set:
        if not isinstance(value, set):
            return False
        # If we have a type argument, check each item
        if hasattr(expected_type, "__args__") and expected_type.__args__:
            item_type = expected_type.__args__[0]
            return all(validate_field_type(item, item_type) for item in value)
        return True
        
    # Handle Optional (Union[T, None])
    if hasattr(expected_type, "__origin__") and expected_type.__origin__ is Union:
        if type(None) in expected_type.__args__:
            if value is None:
                return True
            # Check against other types in the union
            other_types = [t for t in expected_type.__args__ if t is not type(None)]
            if len(other_types) == 1:
                return validate_field_type(value, other_types[0])
            else:
                return any(validate_field_type(value, t) for t in other_types)
    
    # Basic type check
    return isinstance(value, expected_type)


def is_valid_date_format(date_str: str, format: str = '%Y-%m-%d') -> bool:
    """
    Check if a string matches a date format.
    
    Args:
        date_str: Date string to validate
        format: Expected date format
        
    Returns:
        True if valid, False otherwise
    """
    try:
        datetime.strptime(date_str, format)
        return True
    except ValueError:
        return False


def truncate_string(text: str, max_length: int, suffix: str = '...') -> str:
    """
    Truncate a string to a maximum length, adding a suffix if truncated.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
    """
    if not text or len(text) <= max_length:
        return text
        
    return text[:max_length - len(suffix)] + suffix


def clean_dict(data: Dict[str, Any], allowed_keys: Optional[Set[str]] = None) -> Dict[str, Any]:
    """
    Clean a dictionary by removing None values and optionally filtering keys.
    
    Args:
        data: Dictionary to clean
        allowed_keys: Optional set of allowed keys
        
    Returns:
        Cleaned dictionary
    """
    if allowed_keys is not None:
        return {k: v for k, v in data.items() if k in allowed_keys and v is not None}
    else:
        return {k: v for k, v in data.items() if v is not None}


def validate_regex(text: str, pattern: Union[str, Pattern]) -> bool:
    """
    Validate text against a regex pattern.
    
    Args:
        text: Text to validate
        pattern: Regex pattern string or compiled pattern
        
    Returns:
        True if valid, False otherwise
    """
    if not text:
        return False
        
    if isinstance(pattern, str):
        pattern = re.compile(pattern)
        
    return bool(pattern.match(text)) 