"""Flask example with Halt rate limiting."""

from flask import Flask
from halt import RateLimiter, InMemoryStore, presets
from halt.adapters.flask import HaltFlask

app = Flask(__name__)

# Create rate limiter with in-memory store
limiter = RateLimiter(
    store=InMemoryStore(),
    policy=presets.PUBLIC_API
)

# Initialize Flask extension
HaltFlask(app, limiter=limiter)


@app.route("/")
def root():
    """Public endpoint with rate limiting."""
    return {"message": "Hello World", "info": "Rate limited to 100 req/min"}


@app.route("/health")
def health():
    """Health check - automatically exempted from rate limiting."""
    return {"status": "healthy"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
