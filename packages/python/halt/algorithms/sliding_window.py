"""Sliding window rate limiting algorithm."""

import time
from typing import Optional
from halt.core.decision import Decision


class SlidingWindow:
    """Sliding window algorithm for rate limiting.
    
    The sliding window algorithm maintains a rolling count of requests
    over the past window duration. More accurate than fixed window but
    requires more memory.
    """
    
    def __init__(self, limit: int, window: int, precision: int = 10) -> None:
        """Initialize sliding window.
        
        Args:
            limit: Maximum number of requests per window
            window: Time window in seconds
            precision: Number of sub-windows (higher = more accurate, more memory)
        """
        self.limit = limit
        self.window = window
        self.precision = precision
        self.bucket_size = window / precision
    
    def check_and_consume(
        self,
        buckets: dict[int, int],
        cost: int,
        now: Optional[float] = None,
    ) -> tuple[Decision, dict[int, int]]:
        """Check if request is allowed and update buckets.
        
        Args:
            buckets: Dictionary of bucket_id -> count
            cost: Number of requests to consume
            now: Current timestamp (defaults to time.time())
        
        Returns:
            Tuple of (Decision, new_buckets)
        """
        if now is None:
            now = time.time()
        
        # Calculate current bucket
        current_bucket = int(now / self.bucket_size)
        
        # Remove expired buckets (older than window)
        cutoff_bucket = current_bucket - self.precision
        new_buckets = {
            bucket_id: count
            for bucket_id, count in buckets.items()
            if bucket_id > cutoff_bucket
        }
        
        # Count requests in sliding window
        total_count = sum(new_buckets.values())
        
        # Calculate reset time (when oldest bucket expires)
        oldest_bucket = min(new_buckets.keys()) if new_buckets else current_bucket
        reset_at = int((oldest_bucket + self.precision + 1) * self.bucket_size)
        
        # Check if we have capacity
        if total_count + cost <= self.limit:
            # Allow request
            new_buckets[current_bucket] = new_buckets.get(current_bucket, 0) + cost
            remaining = self.limit - (total_count + cost)
            
            return (
                Decision(
                    allowed=True,
                    limit=self.limit,
                    remaining=remaining,
                    reset_at=reset_at,
                ),
                new_buckets,
            )
        else:
            # Block request
            retry_after = int(self.bucket_size) + 1
            
            return (
                Decision(
                    allowed=False,
                    limit=self.limit,
                    remaining=0,
                    reset_at=reset_at,
                    retry_after=retry_after,
                ),
                new_buckets,
            )
    
    def initial_state(self) -> dict[int, int]:
        """Get initial state for a new key.
        
        Returns:
            Empty buckets dictionary
        """
        return {}
