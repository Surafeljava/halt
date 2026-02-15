"""Django middleware adapter for Halt rate limiting."""

from typing import Callable, Optional
from django.http import JsonResponse
from halt.core.limiter import RateLimiter


class HaltMiddleware:
    """Django middleware for rate limiting."""
    
    def __init__(self, get_response: Callable, limiter: RateLimiter) -> None:
        """Initialize middleware.
        
        Args:
            get_response: Next middleware/view
            limiter: RateLimiter instance
        """
        self.get_response = get_response
        self.limiter = limiter
    
    def __call__(self, request):
        """Process request through rate limiter.
        
        Args:
            request: Django request object
        
        Returns:
            Response
        """
        # Check rate limit
        decision = self.limiter.check(request)
        
        if not decision.allowed:
            # Request blocked
            response = JsonResponse(
                {
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": decision.retry_after,
                },
                status=429,
            )
            for key, value in decision.to_headers().items():
                response[key] = value
            return response
        
        # Request allowed - process normally
        response = self.get_response(request)
        
        # Add rate limit headers
        for key, value in decision.to_headers().items():
            response[key] = value
        
        return response


def create_halt_middleware(limiter: RateLimiter) -> type:
    """Create a Django middleware class with the given limiter.
    
    Args:
        limiter: RateLimiter instance
    
    Returns:
        Middleware class
    
    Example:
        ```python
        # settings.py
        from halt import RateLimiter, InMemoryStore, presets
        from halt.adapters.django import create_halt_middleware
        
        limiter = RateLimiter(
            store=InMemoryStore(),
            policy=presets.PUBLIC_API
        )
        
        HaltMiddleware = create_halt_middleware(limiter)
        
        MIDDLEWARE = [
            # ... other middleware
            'myapp.middleware.HaltMiddleware',
        ]
        ```
    """
    class ConfiguredHaltMiddleware:
        def __init__(self, get_response: Callable) -> None:
            self.get_response = get_response
            self.limiter = limiter
        
        def __call__(self, request):
            middleware = HaltMiddleware(self.get_response, self.limiter)
            return middleware(request)
    
    return ConfiguredHaltMiddleware
