# Halt

**Drop-in middleware that enforces consistent rate limits per IP/user/api-key with safe defaults, Redis-backed accuracy, and clean headers.**

## Features

- 🚀 **Multiple Algorithms**: Token Bucket, Fixed Window, Sliding Window
- 🔑 **Flexible Keys**: per-IP, per-user, per-API-key, composite keys
- 💾 **Storage Options**: In-memory (dev) and Redis (prod)
- 🎯 **Framework Support**: FastAPI, Flask, Django, Express, Next.js
- 📊 **Standard Headers**: RateLimit-Limit, RateLimit-Remaining, RateLimit-Reset, Retry-After
- ⚡ **High Performance**: Redis Lua scripts for atomic operations
- 🛡️ **Smart Exemptions**: Health checks, internal networks, allowlists

## Quick Start

### Python (FastAPI)

```python
from fastapi import FastAPI
from halt import RateLimiter, RedisStore, presets
from halt.adapters.fastapi import HaltMiddleware

app = FastAPI()

limiter = RateLimiter(
    store=RedisStore(url="redis://localhost:6379"),
    policy=presets.PUBLIC_API
)

app.add_middleware(HaltMiddleware, limiter=limiter)
```

### TypeScript (Next.js)

```typescript
// app/api/route.ts
import { withHalt, presets } from 'halt/next';

async function handler(req: Request) {
  return Response.json({ message: 'Hello' });
}

export const POST = withHalt(handler, {
  policy: presets.AUTH_ENDPOINTS
});
```

## Packages

- **[Python SDK](./packages/python)** - FastAPI, Flask, Django support
- **[TypeScript SDK](./packages/typescript)** - Express, Next.js support

## Documentation

See the [docs](./docs) folder for detailed documentation.

## License

MIT
