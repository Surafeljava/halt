"""Fixed window rate limiting algorithm."""

import time
from typing import Optional
from halt.core.decision import Decision


class FixedWindow:
    """Fixed window algorithm for rate limiting.
    
    The fixed window algorithm divides time into fixed windows and counts
    requests in each window. Simple but can allow bursts at window boundaries.
    """
    
    def __init__(self, limit: int, window: int) -> None:
        """Initialize fixed window.
        
        Args:
            limit: Maximum number of requests per window
            window: Time window in seconds
        """
        self.limit = limit
        self.window = window
    
    def check_and_consume(
        self,
        current_count: int,
        window_start: float,
        cost: int,
        now: Optional[float] = None,
    ) -> tuple[Decision, int, float]:
        """Check if request is allowed and increment counter.
        
        Args:
            current_count: Current request count in window
            window_start: Start timestamp of current window
            cost: Number of requests to consume
            now: Current timestamp (defaults to time.time())
        
        Returns:
            Tuple of (Decision, new_count, new_window_start)
        """
        if now is None:
            now = time.time()
        
        # Check if we're in a new window
        time_since_start = now - window_start
        if time_since_start >= self.window:
            # New window - reset counter
            current_count = 0
            window_start = now
        
        # Calculate reset time (end of current window)
        reset_at = int(window_start + self.window)
        
        # Check if we have capacity
        if current_count + cost <= self.limit:
            # Allow request
            new_count = current_count + cost
            remaining = self.limit - new_count
            
            return (
                Decision(
                    allowed=True,
                    limit=self.limit,
                    remaining=remaining,
                    reset_at=reset_at,
                ),
                new_count,
                window_start,
            )
        else:
            # Block request
            retry_after = int(reset_at - now) + 1
            
            return (
                Decision(
                    allowed=False,
                    limit=self.limit,
                    remaining=0,
                    reset_at=reset_at,
                    retry_after=retry_after,
                ),
                current_count,
                window_start,
            )
    
    def initial_state(self, now: Optional[float] = None) -> tuple[int, float]:
        """Get initial state for a new key.
        
        Args:
            now: Current timestamp (defaults to time.time())
        
        Returns:
            Tuple of (count, window_start)
        """
        if now is None:
            now = time.time()
        return (0, now)
