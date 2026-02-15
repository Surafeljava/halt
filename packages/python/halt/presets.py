"""Preset rate limiting policies for common use cases."""

from halt.core.policy import Policy, KeyStrategy, Algorithm


# Public API - moderate limits for general public access
PUBLIC_API = Policy(
    name="public_api",
    limit=100,
    window=60,  # 1 minute
    burst=120,
    algorithm=Algorithm.TOKEN_BUCKET,
    key_strategy=KeyStrategy.IP,
)

# Authentication endpoints - strict limits to prevent brute force
AUTH_ENDPOINTS = Policy(
    name="auth_endpoints",
    limit=5,
    window=60,  # 1 minute
    burst=10,
    algorithm=Algorithm.TOKEN_BUCKET,
    key_strategy=KeyStrategy.IP,
    block_duration=300,  # 5 minute cooldown after limit exceeded
)

# Expensive operations - very strict limits for resource-intensive endpoints
EXPENSIVE_OPS = Policy(
    name="expensive_ops",
    limit=10,
    window=3600,  # 1 hour
    burst=15,
    cost=10,  # Each request costs 10 tokens
    algorithm=Algorithm.TOKEN_BUCKET,
    key_strategy=KeyStrategy.USER,
)

# Strict API - for sensitive operations
STRICT_API = Policy(
    name="strict_api",
    limit=20,
    window=60,  # 1 minute
    burst=25,
    algorithm=Algorithm.TOKEN_BUCKET,
    key_strategy=KeyStrategy.API_KEY,
)

# Generous API - for internal or trusted services
GENEROUS_API = Policy(
    name="generous_api",
    limit=1000,
    window=60,  # 1 minute
    burst=1200,
    algorithm=Algorithm.TOKEN_BUCKET,
    key_strategy=KeyStrategy.IP,
)
