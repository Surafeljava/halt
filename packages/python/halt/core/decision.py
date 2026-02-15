"""Decision model for rate limiting results."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Decision:
    """Result of a rate limit check.
    
    Attributes:
        allowed: Whether the request is allowed
        limit: Maximum number of requests allowed in the window
        remaining: Number of requests remaining in the current window
        reset_at: Unix timestamp when the limit resets
        retry_after: Seconds to wait before retrying (only set when blocked)
    """
    
    allowed: bool
    limit: int
    remaining: int
    reset_at: int
    retry_after: Optional[int] = None
    
    def to_headers(self) -> dict[str, str]:
        """Convert decision to standard rate limit headers.
        
        Returns:
            Dictionary of HTTP headers
        """
        headers = {
            "RateLimit-Limit": str(self.limit),
            "RateLimit-Remaining": str(max(0, self.remaining)),
            "RateLimit-Reset": str(self.reset_at),
        }
        
        if not self.allowed and self.retry_after is not None:
            headers["Retry-After"] = str(self.retry_after)
        
        return headers
