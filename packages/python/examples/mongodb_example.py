"""
Example using MongoDB storage backend.
"""

from halt import RateLimiter, Policy, Algorithm, KeyStrategy
from halt.stores.mongodb import MongoDBStore
from halt.adapters.flask import HaltExtension
from flask import Flask, jsonify

# Initialize MongoDB store
store = MongoDBStore(
    connection_string="mongodb://localhost:27017",
    database="halt_db",
    collection="rate_limits"
)

# Create Flask app
app = Flask(__name__)

# Create custom policy
policy = Policy(
    name="api_limit",
    limit=50,
    window=60,
    algorithm=Algorithm.TOKEN_BUCKET,
    key_strategy=KeyStrategy.IP
)

# Initialize rate limiter
limiter = RateLimiter(store=store, policy=policy)

# Add rate limiting extension
halt = HaltExtension(app, limiter)


@app.route("/")
def index():
    return jsonify({"message": "Hello World"})


@app.route("/api/users")
def get_users():
    return jsonify({"users": ["Alice", "Bob", "Charlie"]})


@app.teardown_appcontext
def shutdown(exception=None):
    """Clean up on shutdown."""
    store.close()


if __name__ == "__main__":
    print("Starting Flask with MongoDB storage...")
    print("MongoDB connection: mongodb://localhost:27017")
    print("Rate limit: 50 requests per minute")
    print("\nTry:")
    print("  curl http://localhost:5000/")
    print("  curl http://localhost:5000/api/users")
    
    app.run(host="0.0.0.0", port=5000, debug=True)
