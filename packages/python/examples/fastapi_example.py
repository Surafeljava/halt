"""FastAPI example with Halt rate limiting."""

from fastapi import FastAPI
from halt import RateLimiter, InMemoryStore, presets
from halt.adapters.fastapi import HaltMiddleware

app = FastAPI(title="Halt FastAPI Example")

# Create rate limiter with in-memory store
limiter = RateLimiter(
    store=InMemoryStore(),
    policy=presets.PUBLIC_API
)

# Add middleware
app.add_middleware(HaltMiddleware, limiter=limiter)


@app.get("/")
async def root():
    """Public endpoint with rate limiting."""
    return {"message": "Hello World", "info": "Rate limited to 100 req/min"}


@app.get("/health")
async def health():
    """Health check - automatically exempted from rate limiting."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
