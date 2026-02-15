"""Flask middleware adapter for Halt rate limiting."""

from typing import Optional, Callable
from functools import wraps
from flask import request, jsonify, make_response
from halt.core.limiter import RateLimiter


class HaltFlask:
    """Flask extension for rate limiting."""
    
    def __init__(self, app=None, limiter: Optional[RateLimiter] = None) -> None:
        """Initialize Flask extension.
        
        Args:
            app: Flask application (optional)
            limiter: RateLimiter instance (optional)
        """
        self.limiter = limiter
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app) -> None:
        """Initialize extension with Flask app.
        
        Args:
            app: Flask application
        """
        if self.limiter is None:
            raise ValueError("RateLimiter must be provided")
        
        @app.before_request
        def check_rate_limit():
            decision = self.limiter.check(request)
            
            if not decision.allowed:
                response = make_response(
                    jsonify({
                        "error": "rate_limit_exceeded",
                        "message": "Too many requests. Please try again later.",
                        "retry_after": decision.retry_after,
                    }),
                    429,
                )
                for key, value in decision.to_headers().items():
                    response.headers[key] = value
                return response
        
        @app.after_request
        def add_rate_limit_headers(response):
            # Add headers if not already added (i.e., request was allowed)
            if response.status_code != 429:
                decision = self.limiter.check(request)
                for key, value in decision.to_headers().items():
                    response.headers[key] = value
            return response


def limit(limiter: RateLimiter) -> Callable:
    """Decorator for rate limiting specific Flask routes.
    
    Args:
        limiter: RateLimiter instance
    
    Returns:
        Decorator function
    
    Example:
        ```python
        @app.route('/api/data')
        @limit(my_limiter)
        def get_data():
            return {"data": "..."}
        ```
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            decision = limiter.check(request)
            
            if not decision.allowed:
                response = make_response(
                    jsonify({
                        "error": "rate_limit_exceeded",
                        "message": "Too many requests. Please try again later.",
                        "retry_after": decision.retry_after,
                    }),
                    429,
                )
                for key, value in decision.to_headers().items():
                    response.headers[key] = value
                return response
            
            # Call the original function
            result = f(*args, **kwargs)
            
            # Add headers to response
            if isinstance(result, tuple):
                response = make_response(*result)
            else:
                response = make_response(result)
            
            for key, value in decision.to_headers().items():
                response.headers[key] = value
            
            return response
        
        return decorated_function
    return decorator
