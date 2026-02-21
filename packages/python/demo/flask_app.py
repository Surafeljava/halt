"""Minimal Flask demo app using halt-rate.

Run:
  pip install flask halt-rate
  python demo/flask_app.py
"""

from flask import Flask, jsonify

from halt import RateLimiter, InMemoryStore, Policy, KeyStrategy, Algorithm
from halt.adapters.flask import HaltFlask

app = Flask(__name__)

# Minimal, low limits so you can see 429s quickly.
# 3 requests per 10 seconds per IP.
policy = Policy(
    name="demo",
    limit=3,
    window=10,
    burst=3,
    algorithm=Algorithm.TOKEN_BUCKET,
    key_strategy=KeyStrategy.IP,
)

limiter = RateLimiter(
    store=InMemoryStore(),
    policy=policy,
    # Localhost is a private IP; disable exemption so you can see limits locally.
    exempt_private_ips=False,
)

# Attach middleware to Flask
HaltFlask(app, limiter=limiter)


@app.get("/limited")
def limited():
    # Avoid default health-check paths like /ping to ensure rate limiting applies.
    return jsonify({"ok": True, "message": "rate limited endpoint"})


if __name__ == "__main__":
    # Local dev server
    app.run(host="127.0.0.1", port=5000, debug=True)
