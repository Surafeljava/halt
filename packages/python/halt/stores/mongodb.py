"""MongoDB storage backend for rate limiting."""

import time
from typing import Any, Optional
from datetime import datetime, timedelta

try:
    from pymongo import MongoClient, ASCENDING
    from pymongo.errors import DuplicateKeyError
except ImportError:
    raise ImportError(
        "MongoDB storage requires pymongo. "
        "Install with: pip install 'halt[mongodb]' or pip install pymongo"
    )


class MongoDBStore:
    """MongoDB-backed storage for rate limiting state.
    
    Features:
    - Document-based storage
    - TTL indexes for automatic expiration
    - Atomic updates via findAndModify
    - Connection pooling
    """
    
    def __init__(
        self,
        connection_string: str,
        database: str = "halt",
        collection: str = "rate_limits",
        **kwargs
    ) -> None:
        """Initialize MongoDB store.
        
        Args:
            connection_string: MongoDB connection string (e.g., "mongodb://localhost:27017")
            database: Database name
            collection: Collection name
            **kwargs: Additional arguments for MongoClient
        """
        self.client = MongoClient(connection_string, **kwargs)
        self.db = self.client[database]
        self.collection = self.db[collection]
        self._ensure_indexes()
    
    def _ensure_indexes(self) -> None:
        """Create indexes for efficient queries."""
        # Create TTL index for automatic expiration
        self.collection.create_index(
            "expires_at",
            expireAfterSeconds=0,
            name="ttl_index"
        )
        
        # Create index on key for fast lookups
        self.collection.create_index("key", unique=True, name="key_index")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from storage.
        
        Args:
            key: Storage key
            
        Returns:
            Stored value or None if not found or expired
        """
        doc = self.collection.find_one(
            {
                "key": key,
                "expires_at": {"$gt": datetime.utcnow()}
            }
        )
        
        if doc:
            state = doc.get("state")
            # Convert list back to tuple if needed
            if isinstance(state, list):
                return tuple(state)
            return state
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in storage.
        
        Args:
            key: Storage key
            value: Value to store
            ttl: Time to live in seconds (optional)
        """
        if ttl is None:
            ttl = 3600  # Default 1 hour
        
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        # Serialize value (convert tuples to lists for MongoDB)
        if isinstance(value, tuple):
            serialized_value = list(value)
        else:
            serialized_value = value
        
        # Upsert document
        self.collection.update_one(
            {"key": key},
            {
                "$set": {
                    "state": serialized_value,
                    "expires_at": expires_at,
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )
    
    def delete(self, key: str) -> None:
        """Delete key from storage.
        
        Args:
            key: Storage key
        """
        self.collection.delete_one({"key": key})
    
    def cleanup_expired(self) -> int:
        """Remove expired keys from storage.
        
        Note: MongoDB TTL index handles this automatically,
        but this method can be used for manual cleanup.
        
        Returns:
            Number of keys deleted
        """
        result = self.collection.delete_many(
            {"expires_at": {"$lte": datetime.utcnow()}}
        )
        return result.deleted_count
    
    def close(self) -> None:
        """Close MongoDB connection."""
        self.client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
