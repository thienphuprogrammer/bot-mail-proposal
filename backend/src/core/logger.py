import logging
import os
import sys
from typing import Optional

def get_logger(name: str, log_level: Optional[str] = None) -> logging.Logger:
    """
    Get a logger with the specified name and log level.
    
    Args:
        name: The name of the logger.
        log_level: The log level to use. If None, the log level is determined from the
            environment variable LOG_LEVEL or defaults to INFO.
    
    Returns:
        A logger instance.
    """
    # Set log level from environment variable or default to INFO
    if log_level is None:
        log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Set log level
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    logger.setLevel(numeric_level)
    
    # Create handler if the logger doesn't already have one
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger 