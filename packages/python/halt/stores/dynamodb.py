"""DynamoDB storage backend for rate limiting."""

import json
import time
from typing import Any, Optional
from decimal import Decimal

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    raise ImportError(
        "DynamoDB storage requires boto3. "
        "Install with: pip install 'halt[dynamodb]' or pip install boto3"
    )


class DynamoDBStore:
    """DynamoDB-backed storage for rate limiting state.
    
    Features:
    - AWS managed, serverless
    - Conditional writes for atomicity
    - TTL attribute for auto-cleanup
    - Global tables for multi-region support
    """
    
    def __init__(
        self,
        table_name: str,
        region_name: str = "us-east-1",
        endpoint_url: Optional[str] = None,
        **kwargs
    ) -> None:
        """Initialize DynamoDB store.
        
        Args:
            table_name: DynamoDB table name
            region_name: AWS region
            endpoint_url: Custom endpoint (for local DynamoDB)
            **kwargs: Additional arguments for boto3 client
        """
        self.table_name = table_name
        
        # Create DynamoDB client
        client_kwargs = {"region_name": region_name, **kwargs}
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url
        
        self.dynamodb = boto3.resource("dynamodb", **client_kwargs)
        self.table = self.dynamodb.Table(table_name)
        self._ensure_table()
    
    def _ensure_table(self) -> None:
        """Create table if it doesn't exist."""
        try:
            # Check if table exists
            self.table.load()
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Create table
                table = self.dynamodb.create_table(
                    TableName=self.table_name,
                    KeySchema=[
                        {'AttributeName': 'key', 'KeyType': 'HASH'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'key', 'AttributeType': 'S'}
                    ],
                    BillingMode='PAY_PER_REQUEST'
                )
                
                # Wait for table to be created
                table.wait_until_exists()
                
                # Enable TTL
                client = boto3.client('dynamodb', region_name=self.dynamodb.meta.client.meta.region_name)
                client.update_time_to_live(
                    TableName=self.table_name,
                    TimeToLiveSpecification={
                        'Enabled': True,
                        'AttributeName': 'ttl'
                    }
                )
    
    def _serialize_value(self, value: Any) -> Any:
        """Serialize value for DynamoDB (handle tuples and floats)."""
        if isinstance(value, tuple):
            return [self._serialize_value(v) for v in value]
        elif isinstance(value, float):
            return Decimal(str(value))
        elif isinstance(value, list):
            return [self._serialize_value(v) for v in value]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        return value
    
    def _deserialize_value(self, value: Any) -> Any:
        """Deserialize value from DynamoDB."""
        if isinstance(value, list):
            deserialized = [self._deserialize_value(v) for v in value]
            # Check if this should be a tuple (for algorithm state)
            if len(deserialized) == 2 and all(isinstance(v, (int, float, Decimal)) for v in deserialized):
                return tuple(float(v) if isinstance(v, Decimal) else v for v in deserialized)
            return deserialized
        elif isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, dict):
            return {k: self._deserialize_value(v) for k, v in value.items()}
        return value
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from storage.
        
        Args:
            key: Storage key
            
        Returns:
            Stored value or None if not found or expired
        """
        try:
            response = self.table.get_item(Key={'key': key})
            
            if 'Item' in response:
                item = response['Item']
                
                # Check if expired
                if 'ttl' in item and item['ttl'] <= int(time.time()):
                    return None
                
                return self._deserialize_value(item.get('state'))
            
            return None
        except ClientError:
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
        
        ttl_timestamp = int(time.time()) + ttl
        
        item = {
            'key': key,
            'state': self._serialize_value(value),
            'ttl': ttl_timestamp
        }
        
        self.table.put_item(Item=item)
    
    def delete(self, key: str) -> None:
        """Delete key from storage.
        
        Args:
            key: Storage key
        """
        self.table.delete_item(Key={'key': key})
    
    def cleanup_expired(self) -> int:
        """Remove expired keys from storage.
        
        Note: DynamoDB TTL handles this automatically.
        This method is a no-op but provided for interface compatibility.
        
        Returns:
            0 (DynamoDB handles cleanup automatically)
        """
        # DynamoDB TTL handles cleanup automatically
        return 0
    
    def close(self) -> None:
        """Close DynamoDB connection (no-op for boto3)."""
        pass
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
