"""
Example using PostgreSQL storage backend.
"""

from halt import RateLimiter, Policy, Algorithm, KeyStrategy, presets
from halt.stores.postgres import PostgresStore
from halt.adapters.fastapi import HaltMiddleware
from fastapi import FastAPI

# Initialize PostgreSQL store
store = PostgresStore(
    connection_string="postgresql://user:password@localhost:5432/halt_db",
    table_name="rate_limits",
    min_connections=2,
    max_connections=10
)

# Create FastAPI app
app = FastAPI()

# Add rate limiting middleware
limiter = RateLimiter(
    store=store,
    policy=presets.PUBLIC_API
)

app.add_middleware(HaltMiddleware, limiter=limiter)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/api/data")
async def get_data():
    return {"data": [1, 2, 3, 4, 5]}


@app.on_event("shutdown")
async def shutdown():
    """Clean up on shutdown."""
    store.close()


if __name__ == "__main__":
    import uvicorn
    
    print("Starting FastAPI with PostgreSQL storage...")
    print("PostgreSQL connection: postgresql://localhost:5432/halt_db")
    print("Rate limit: 100 requests per minute")
    print("\nTry:")
    print("  curl http://localhost:8000/")
    print("  curl http://localhost:8000/api/data")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
