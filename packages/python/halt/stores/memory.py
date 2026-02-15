"""In-memory storage backend for rate limiting."""

import time
import threading
from typing import Any, Optional, Dict
from collections import defaultdict


class InMemoryStore:
    """Thread-safe in-memory storage with TTL support.
    
    Suitable for development and testing. Not recommended for production
    with multiple processes or servers.
    """
    
    def __init__(self) -> None:
        """Initialize in-memory store."""
        self._data: Dict[str, Any] = {}
        self._expiry: Dict[str, float] = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value for key.
        
        Args:
            key: Storage key
        
        Returns:
            Value or None if not found or expired
        """
        with self._lock:
            self._cleanup_expired(key)
            return self._data.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value for key with optional TTL.
        
        Args:
            key: Storage key
            value: Value to store
            ttl: Time to live in seconds (None = no expiry)
        """
        with self._lock:
            self._data[key] = value
            if ttl is not None:
                self._expiry[key] = time.time() + ttl
            elif key in self._expiry:
                del self._expiry[key]
    
    def increment(self, key: str, delta: int = 1, ttl: Optional[int] = None) -> int:
        """Increment value for key atomically.
        
        Args:
            key: Storage key
            delta: Amount to increment by
            ttl: Time to live in seconds (only set if key doesn't exist)
        
        Returns:
            New value after increment
        """
        with self._lock:
            self._cleanup_expired(key)
            current = self._data.get(key, 0)
            if not isinstance(current, (int, float)):
                current = 0
            new_value = current + delta
            self._data[key] = new_value
            
            # Set TTL only if key didn't exist
            if key not in self._expiry and ttl is not None:
                self._expiry[key] = time.time() + ttl
            
            return int(new_value)
    
    def delete(self, key: str) -> None:
        """Delete key from storage.
        
        Args:
            key: Storage key
        """
        with self._lock:
            self._data.pop(key, None)
            self._expiry.pop(key, None)
    
    def _cleanup_expired(self, key: str) -> None:
        """Remove key if expired."""
        if key in self._expiry and time.time() >= self._expiry[key]:
            self._data.pop(key, None)
            self._expiry.pop(key, None)
    
    def cleanup_all_expired(self) -> int:
        """Clean up all expired keys.
        
        Returns:
            Number of keys cleaned up
        """
        with self._lock:
            now = time.time()
            expired_keys = [k for k, exp in self._expiry.items() if now >= exp]
            for key in expired_keys:
                self._data.pop(key, None)
                self._expiry.pop(key, None)
            return len(expired_keys)
