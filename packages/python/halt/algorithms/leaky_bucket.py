"""Leaky bucket rate limiting algorithm."""

import time
from typing import Optional
from halt.core.decision import Decision


class LeakyBucket:
    """Leaky bucket algorithm for rate limiting.
    
    The leaky bucket algorithm processes requests at a constant rate,
    smoothing out bursts. Requests are added to a bucket and leak out
    at a constant rate. Excellent for traffic shaping.
    """
    
    def __init__(self, capacity: int, leak_rate: float, window: int) -> None:
        """Initialize leaky bucket.
        
        Args:
            capacity: Maximum bucket capacity (max burst size)
            leak_rate: Rate at which requests leak (requests per second)
            window: Time window for rate calculation (seconds)
        """
        self.capacity = capacity
        self.leak_rate = leak_rate  # requests per second
        self.window = window
    
    def check_and_consume(
        self,
        current_level: float,
        last_leak: float,
        cost: int,
        now: Optional[float] = None,
    ) -> tuple[Decision, float, float]:
        """Check if request is allowed and update bucket level.
        
        Args:
            current_level: Current water level in bucket
            last_leak: Timestamp of last leak
            cost: Number of requests to add
            now: Current timestamp (defaults to time.time())
        
        Returns:
            Tuple of (Decision, new_level, new_last_leak)
        """
        if now is None:
            now = time.time()
        
        # Calculate how much has leaked since last check
        elapsed = now - last_leak
        leaked = elapsed * self.leak_rate
        
        # Update bucket level (can't go below 0)
        new_level = max(0, current_level - leaked)
        
        # Calculate when bucket will be empty
        if new_level > 0:
            time_to_empty = new_level / self.leak_rate
            reset_at = int(now + time_to_empty)
        else:
            reset_at = int(now)
        
        # Check if we have capacity
        if new_level + cost <= self.capacity:
            # Allow request - add to bucket
            new_level += cost
            remaining = int(self.capacity - new_level)
            
            return (
                Decision(
                    allowed=True,
                    limit=self.capacity,
                    remaining=remaining,
                    reset_at=reset_at,
                ),
                new_level,
                now,
            )
        else:
            # Block request - bucket is full
            # Calculate when there will be enough capacity
            space_needed = (new_level + cost) - self.capacity
            retry_after = int(space_needed / self.leak_rate) + 1
            
            return (
                Decision(
                    allowed=False,
                    limit=self.capacity,
                    remaining=0,
                    reset_at=reset_at,
                    retry_after=retry_after,
                ),
                new_level,
                now,
            )
    
    def initial_state(self, now: Optional[float] = None) -> tuple[float, float]:
        """Get initial state for a new key.
        
        Args:
            now: Current timestamp (defaults to time.time())
        
        Returns:
            Tuple of (level, last_leak)
        """
        if now is None:
            now = time.time()
        return (0.0, now)
