"""Memcached storage backend for rate limiting."""

import pickle
import time
from typing import Any, Optional

try:
    from pymemcache.client.base import Client
    from pymemcache.client.hash import HashClient
except ImportError:
    raise ImportError(
        "Memcached storage requires pymemcache. "
        "Install with: pip install 'halt[memcached]' or pip install pymemcache"
    )


class MemcachedStore:
    """Memcached-backed storage for rate limiting state.
    
    Features:
    - Distributed caching
    - Fast in-memory operations
    - CAS (Compare-And-Swap) for atomicity
    - Connection pooling
    """
    
    def __init__(
        self,
        servers: str | list[tuple[str, int]] = "localhost:11211",
        **kwargs
    ) -> None:
        """Initialize Memcached store.
        
        Args:
            servers: Single server string "host:port" or list of (host, port) tuples
            **kwargs: Additional arguments for pymemcache client
        """
        # Parse servers
        if isinstance(servers, str):
            host, port = servers.split(":")
            self.client = Client(
                (host, int(port)),
                serializer=self._serialize,
                deserializer=self._deserialize,
                **kwargs
            )
        else:
            # Multiple servers - use HashClient for distribution
            self.client = HashClient(
                servers,
                serializer=self._serialize,
                deserializer=self._deserialize,
                **kwargs
            )
    
    @staticmethod
    def _serialize(key: str, value: Any) -> tuple[bytes, int]:
        """Serialize value for Memcached.
        
        Args:
            key: Cache key
            value: Value to serialize
            
        Returns:
            Tuple of (serialized_value, flags)
        """
        return pickle.dumps(value), 0
    
    @staticmethod
    def _deserialize(key: str, value: bytes, flags: int) -> Any:
        """Deserialize value from Memcached.
        
        Args:
            key: Cache key
            value: Serialized value
            flags: Flags from Memcached
            
        Returns:
            Deserialized value
        """
        return pickle.loads(value)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from storage.
        
        Args:
            key: Storage key
            
        Returns:
            Stored value or None if not found or expired
        """
        return self.client.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in storage.
        
        Args:
            key: Storage key
            value: Value to store
            ttl: Time to live in seconds (optional)
        """
        if ttl is None:
            ttl = 3600  # Default 1 hour
        
        self.client.set(key, value, expire=ttl)
    
    def delete(self, key: str) -> None:
        """Delete key from storage.
        
        Args:
            key: Storage key
        """
        self.client.delete(key)
    
    def cas_set(self, key: str, value: Any, cas: int, ttl: Optional[int] = None) -> bool:
        """Set value using Compare-And-Swap for atomicity.
        
        Args:
            key: Storage key
            value: Value to store
            cas: CAS token from previous get
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if successful, False if CAS failed
        """
        if ttl is None:
            ttl = 3600
        
        return self.client.cas(key, value, cas, expire=ttl)
    
    def gets(self, key: str) -> tuple[Optional[Any], Optional[int]]:
        """Get value with CAS token.
        
        Args:
            key: Storage key
            
        Returns:
            Tuple of (value, cas_token)
        """
        result = self.client.gets(key)
        if result is None:
            return None, None
        return result
    
    def cleanup_expired(self) -> int:
        """Remove expired keys from storage.
        
        Note: Memcached handles expiration automatically.
        This method is a no-op but provided for interface compatibility.
        
        Returns:
            0 (Memcached handles cleanup automatically)
        """
        # Memcached handles expiration automatically
        return 0
    
    def close(self) -> None:
        """Close Memcached connection."""
        self.client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
