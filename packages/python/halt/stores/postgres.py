"""PostgreSQL storage backend for rate limiting."""

import json
import time
from typing import Any, Optional
from contextlib import contextmanager

try:
    import psycopg
    from psycopg.rows import dict_row
    from psycopg_pool import ConnectionPool
except ImportError:
    raise ImportError(
        "PostgreSQL storage requires psycopg. "
        "Install with: pip install 'halt[postgres]' or pip install psycopg[binary] psycopg-pool"
    )


class PostgresStore:
    """PostgreSQL-backed storage for rate limiting state.
    
    Features:
    - ACID transactions for consistency
    - Automatic cleanup of expired keys
    - Connection pooling
    - Thread-safe operations
    """
    
    def __init__(
        self,
        connection_string: str,
        table_name: str = "rate_limit_state",
        min_connections: int = 2,
        max_connections: int = 10,
    ) -> None:
        """Initialize PostgreSQL store.
        
        Args:
            connection_string: PostgreSQL connection string (e.g., "postgresql://user:pass@localhost/db")
            table_name: Name of the table to store rate limit state
            min_connections: Minimum number of connections in pool
            max_connections: Maximum number of connections in pool
        """
        self.table_name = table_name
        self.pool = ConnectionPool(
            connection_string,
            min_size=min_connections,
            max_size=max_connections,
        )
        self._ensure_table()
    
    def _ensure_table(self) -> None:
        """Create table if it doesn't exist."""
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        key VARCHAR(255) PRIMARY KEY,
                        state JSONB NOT NULL,
                        expires_at BIGINT NOT NULL
                    )
                """)
                
                # Create index for efficient cleanup
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.table_name}_expires_at
                    ON {self.table_name}(expires_at)
                """)
                
                conn.commit()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from storage.
        
        Args:
            key: Storage key
            
        Returns:
            Stored value or None if not found or expired
        """
        now = int(time.time())
        
        with self.pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"""
                    SELECT state FROM {self.table_name}
                    WHERE key = %s AND expires_at > %s
                    """,
                    (key, now)
                )
                
                row = cur.fetchone()
                if row:
                    # Deserialize state (handle tuples for algorithm state)
                    state = row['state']
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
        
        expires_at = int(time.time()) + ttl
        
        # Serialize value (convert tuples to lists for JSON)
        if isinstance(value, tuple):
            serialized_value = list(value)
        else:
            serialized_value = value
        
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {self.table_name} (key, state, expires_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (key) DO UPDATE
                    SET state = EXCLUDED.state, expires_at = EXCLUDED.expires_at
                    """,
                    (key, json.dumps(serialized_value), expires_at)
                )
                conn.commit()
    
    def delete(self, key: str) -> None:
        """Delete key from storage.
        
        Args:
            key: Storage key
        """
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"DELETE FROM {self.table_name} WHERE key = %s",
                    (key,)
                )
                conn.commit()
    
    def cleanup_expired(self) -> int:
        """Remove expired keys from storage.
        
        Returns:
            Number of keys deleted
        """
        now = int(time.time())
        
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"DELETE FROM {self.table_name} WHERE expires_at <= %s",
                    (now,)
                )
                deleted = cur.rowcount
                conn.commit()
                return deleted
    
    def close(self) -> None:
        """Close connection pool."""
        self.pool.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
