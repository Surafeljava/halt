"""Utility functions for extracting rate limit keys from requests."""

from typing import Optional, Any
import ipaddress


# Default health check paths
HEALTH_CHECK_PATHS = {"/health", "/ping", "/ready", "/healthz", "/livez"}

# Private IP ranges
PRIVATE_IP_RANGES = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]


def extract_ip(request: Any, trusted_proxies: Optional[list[str]] = None) -> Optional[str]:
    """Extract client IP from request, respecting X-Forwarded-For if from trusted proxy.
    
    Args:
        request: Request object (framework-specific)
        trusted_proxies: List of trusted proxy IPs/networks
    
    Returns:
        Client IP address or None
    """
    # Try to get direct client IP
    client_ip = None
    
    # Handle different framework request objects
    if hasattr(request, "client") and hasattr(request.client, "host"):
        # FastAPI/Starlette
        client_ip = request.client.host
    elif hasattr(request, "remote_addr"):
        # Flask/Django
        client_ip = request.remote_addr
    elif hasattr(request, "socket") and hasattr(request.socket, "remoteAddress"):
        # Express (via headers)
        client_ip = getattr(request.socket, "remoteAddress", None)
    
    if not client_ip:
        return None
    
    # Check if we should trust X-Forwarded-For
    if trusted_proxies and _is_trusted_proxy(client_ip, trusted_proxies):
        forwarded_for = _get_forwarded_for(request)
        if forwarded_for:
            return forwarded_for
    
    return client_ip


def _get_forwarded_for(request: Any) -> Optional[str]:
    """Extract first IP from X-Forwarded-For header."""
    forwarded = None
    
    if hasattr(request, "headers"):
        # Most frameworks
        headers = request.headers
        forwarded = headers.get("X-Forwarded-For") or headers.get("x-forwarded-for")
    
    if forwarded:
        # Take the first IP (client IP)
        return forwarded.split(",")[0].strip()
    
    return None


def _is_trusted_proxy(ip: str, trusted_proxies: list[str]) -> bool:
    """Check if IP is in trusted proxy list."""
    try:
        ip_addr = ipaddress.ip_address(ip)
        for proxy in trusted_proxies:
            try:
                if "/" in proxy:
                    # Network range
                    if ip_addr in ipaddress.ip_network(proxy):
                        return True
                else:
                    # Single IP
                    if ip_addr == ipaddress.ip_address(proxy):
                        return True
            except ValueError:
                continue
        return False
    except ValueError:
        return False


def is_private_ip(ip: str) -> bool:
    """Check if IP is in private range."""
    try:
        ip_addr = ipaddress.ip_address(ip)
        return any(ip_addr in network for network in PRIVATE_IP_RANGES)
    except ValueError:
        return False


def is_health_check(path: str) -> bool:
    """Check if path is a health check endpoint."""
    return path in HEALTH_CHECK_PATHS


def extract_user_id(request: Any) -> Optional[str]:
    """Extract user ID from request (framework-specific).
    
    Args:
        request: Request object
    
    Returns:
        User ID or None
    """
    # Try common patterns
    if hasattr(request, "user") and hasattr(request.user, "id"):
        return str(request.user.id)
    
    if hasattr(request, "state") and hasattr(request.state, "user_id"):
        return str(request.state.user_id)
    
    return None


def extract_api_key(request: Any) -> Optional[str]:
    """Extract API key from request headers.
    
    Args:
        request: Request object
    
    Returns:
        API key or None
    """
    if hasattr(request, "headers"):
        headers = request.headers
        # Try common header names
        for header in ["X-API-Key", "x-api-key", "Authorization"]:
            value = headers.get(header)
            if value:
                # Handle Bearer tokens
                if value.startswith("Bearer "):
                    return value[7:]
                return value
    
    return None
