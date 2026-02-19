"""Graphene middleware adapter for Halt rate limiting.

Usage:
from halt.adapters.graphql import HaltGrapheneMiddleware

middleware = [HaltGrapheneMiddleware(limiter)]
schema = graphene.Schema(query=Query, middleware=middleware)
"""
from typing import Any, Optional


class HaltGrapheneMiddleware:
    def __init__(self, limiter: Any, resource_extractor: Optional[Any] = None):
        self.limiter = limiter
        self.resource_extractor = resource_extractor

    def resolve(self, next_, root, info, **kwargs):
        """Graphene middleware entrypoint. Runs before resolver execution."""
        # Build a request-like object the limiter understands
        request = getattr(info.context, "request", info.context)

        if self.resource_extractor:
            setattr(request, "resource", self.resource_extractor(info))

        # Limiter may be sync; handle both
        try:
            decision = self.limiter.check(request)
        except TypeError:
            # Async resolver - call coroutine
            import asyncio

            decision = asyncio.get_event_loop().run_until_complete(self.limiter.check(request))

        if not decision.allowed:
            # Raise an error to short-circuit resolver execution
            raise Exception("rate_limit_exceeded: Too many requests. Please try again later.")

        # Optionally attach headers on context for HTTP frameworks
        if hasattr(info.context, "response"):
            try:
                headers = getattr(info.context, "response").headers
                headers["RateLimit-Limit"] = str(decision.limit)
                headers["RateLimit-Remaining"] = str(max(0, decision.remaining))
                headers["RateLimit-Reset"] = str(decision.reset_at if hasattr(decision, "reset_at") else decision.resetAt)
            except Exception:
                pass

        return next_(root, info, **kwargs)
