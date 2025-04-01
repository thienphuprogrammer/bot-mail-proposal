"""
Rate limiting utilities for API endpoints.
"""

import time
from typing import Dict, Tuple, Optional, Callable, Any, List
import logging
from functools import wraps
from collections import deque

from core.const import DEFAULT_RATE_LIMIT, ADMIN_RATE_LIMIT, UserRole

# Setup logger
logger = logging.getLogger(__name__)


class TokenBucket:
    """
    Token bucket algorithm implementation for rate limiting.
    """
    
    def __init__(self, rate: float, capacity: float):
        """
        Initialize a token bucket.
        
        Args:
            rate: Rate at which tokens are added to the bucket (tokens/second)
            capacity: Maximum capacity of the bucket
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.time()
        
    def consume(self, tokens: float = 1.0) -> bool:
        """
        Attempt to consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False otherwise
        """
        now = time.time()
        # Refill tokens based on time elapsed
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now
        
        # Try to consume tokens
        if tokens <= self.tokens:
            self.tokens -= tokens
            return True
        else:
            return False


class RateLimiter:
    """
    Rate limiter for API endpoints that supports different rate limits for different users.
    """
    
    def __init__(self):
        """Initialize the rate limiter."""
        # Map of user ID to token bucket
        self.buckets: Dict[str, TokenBucket] = {}
        # Map of user ID to rate limit overrides
        self.user_limits: Dict[str, float] = {}
        
    def get_bucket(self, user_id: str, role: str = UserRole.STAFF) -> TokenBucket:
        """
        Get the token bucket for a user, creating it if it doesn't exist.
        
        Args:
            user_id: User ID
            role: User role (admin, staff, client)
            
        Returns:
            Token bucket for the user
        """
        if user_id not in self.buckets:
            # Get the appropriate rate limit
            rate_limit = self.user_limits.get(user_id, None)
            
            if rate_limit is None:
                # Use role-based rate limit if no user-specific limit
                if role == UserRole.ADMIN:
                    rate_limit = ADMIN_RATE_LIMIT
                else:
                    rate_limit = DEFAULT_RATE_LIMIT
            
            # Convert from requests/minute to tokens/second
            rate = rate_limit / 60.0
            # Allow bursts up to 25% of the per-minute limit
            capacity = max(1, rate_limit * 0.25)
            
            self.buckets[user_id] = TokenBucket(rate, capacity)
            
        return self.buckets[user_id]
        
    def set_user_limit(self, user_id: str, limit: float) -> None:
        """
        Set a custom rate limit for a user.
        
        Args:
            user_id: User ID
            limit: Rate limit in requests per minute
        """
        self.user_limits[user_id] = limit
        # Update the bucket if it exists
        if user_id in self.buckets:
            rate = limit / 60.0
            capacity = max(1, limit * 0.25)
            self.buckets[user_id] = TokenBucket(rate, capacity)
        
    def check_rate_limit(self, user_id: str, tokens: float = 1.0, role: str = UserRole.STAFF) -> Tuple[bool, Optional[float]]:
        """
        Check if a user is rate-limited.
        
        Args:
            user_id: User ID
            tokens: Number of tokens to consume
            role: User role
            
        Returns:
            Tuple of (allowed, retry_after)
                allowed: True if request is allowed, False otherwise
                retry_after: Seconds to wait before retrying, or None if allowed
        """
        bucket = self.get_bucket(user_id, role)
        
        if bucket.consume(tokens):
            return True, None
        else:
            # Calculate retry time (how long until 1 token is available)
            tokens_needed = tokens - bucket.tokens
            retry_after = tokens_needed / bucket.rate
            return False, retry_after
        
    def cleanup(self, max_idle_time: float = 3600.0) -> None:
        """
        Clean up idle buckets to prevent memory leaks.
        
        Args:
            max_idle_time: Maximum idle time in seconds
        """
        now = time.time()
        to_remove = []
        
        for user_id, bucket in self.buckets.items():
            # If bucket is full and hasn't been used in a while, remove it
            if bucket.tokens >= bucket.capacity and (now - bucket.last_refill) > max_idle_time:
                to_remove.append(user_id)
                
        for user_id in to_remove:
            del self.buckets[user_id]
            
        if to_remove:
            logger.debug(f"Cleaned up {len(to_remove)} idle rate limit buckets")


class SlidingWindowRateLimiter:
    """
    Sliding window implementation for rate limiting.
    More accurate than token bucket but uses more memory.
    """
    
    def __init__(self):
        """Initialize the rate limiter."""
        # Map of user ID to list of request timestamps
        self.requests: Dict[str, deque] = {}
        # Map of user ID to rate limit overrides
        self.user_limits: Dict[str, int] = {}
        
    def check_rate_limit(self, user_id: str, role: str = UserRole.STAFF, window: int = 60) -> Tuple[bool, Optional[float]]:
        """
        Check if a user is rate-limited.
        
        Args:
            user_id: User ID
            role: User role
            window: Time window in seconds
            
        Returns:
            Tuple of (allowed, retry_after)
                allowed: True if request is allowed, False otherwise
                retry_after: Seconds to wait before retrying, or None if allowed
        """
        # Get the appropriate rate limit
        rate_limit = self.user_limits.get(user_id, None)
        
        if rate_limit is None:
            # Use role-based rate limit if no user-specific limit
            if role == UserRole.ADMIN:
                rate_limit = ADMIN_RATE_LIMIT
            else:
                rate_limit = DEFAULT_RATE_LIMIT
        
        # Get or create request queue for user
        if user_id not in self.requests:
            self.requests[user_id] = deque()
        
        now = time.time()
        requests = self.requests[user_id]
        
        # Remove expired timestamps
        cutoff = now - window
        while requests and requests[0] < cutoff:
            requests.popleft()
        
        # Check if we're at the rate limit
        if len(requests) < rate_limit:
            # Allow request and add timestamp
            requests.append(now)
            return True, None
        else:
            # Calculate time to wait until oldest request expires
            retry_after = requests[0] - cutoff
            return False, max(0.1, retry_after)
        
    def set_user_limit(self, user_id: str, limit: int) -> None:
        """
        Set a custom rate limit for a user.
        
        Args:
            user_id: User ID
            limit: Rate limit in requests per minute
        """
        self.user_limits[user_id] = limit
        
    def cleanup(self, max_idle_time: float = 3600.0) -> None:
        """
        Clean up idle request queues to prevent memory leaks.
        
        Args:
            max_idle_time: Maximum idle time in seconds
        """
        now = time.time()
        to_remove = []
        
        for user_id, requests in self.requests.items():
            # If no requests or last request was a long time ago
            if not requests or (now - requests[-1]) > max_idle_time:
                to_remove.append(user_id)
                
        for user_id in to_remove:
            del self.requests[user_id]
            
        if to_remove:
            logger.debug(f"Cleaned up {len(to_remove)} idle rate limit queues")


# Singleton instances
token_bucket_limiter = RateLimiter()
sliding_window_limiter = SlidingWindowRateLimiter()


def rate_limit_decorator(
    limiter: Optional[RateLimiter] = None,
    get_user_id: Callable[[Any], str] = lambda request: getattr(request, "user", {}).get("id", "anonymous"),
    get_user_role: Callable[[Any], str] = lambda request: getattr(request, "user", {}).get("role", UserRole.STAFF),
    tokens: float = 1.0
):
    """
    Decorator for rate limiting API endpoints.
    
    Args:
        limiter: Rate limiter to use (defaults to token_bucket_limiter)
        get_user_id: Function to extract user ID from request
        get_user_role: Function to extract user role from request
        tokens: Number of tokens to consume
        
    Returns:
        Decorator function
    """
    if limiter is None:
        limiter = token_bucket_limiter
        
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find request object - typically first arg or in kwargs
            request = None
            if args and hasattr(args[0], "headers"):
                request = args[0]
            else:
                for arg in args:
                    if hasattr(arg, "headers"):
                        request = arg
                        break
                        
            if request is None:
                for _, value in kwargs.items():
                    if hasattr(value, "headers"):
                        request = value
                        break
            
            if request is None:
                logger.warning("Could not find request object for rate limiting")
                return await func(*args, **kwargs)
            
            # Get user info for rate limiting
            user_id = get_user_id(request)
            user_role = get_user_role(request)
            
            # Check rate limit
            allowed, retry_after = limiter.check_rate_limit(user_id, tokens, user_role)
            
            if allowed:
                return await func(*args, **kwargs)
            else:
                # Return rate limit error
                from fastapi import HTTPException
                from starlette.status import HTTP_429_TOO_MANY_REQUESTS
                
                headers = {"Retry-After": str(int(retry_after))}
                raise HTTPException(
                    status_code=HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers=headers
                )
                
        return wrapper
        
    return decorator 