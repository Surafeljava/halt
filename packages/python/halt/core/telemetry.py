"""Telemetry hooks for observability and monitoring."""

from typing import Any, Optional, Protocol
from halt.core.decision import Decision
from halt.core.quota import Quota
from halt.core.penalty import Penalty


class TelemetryHooks(Protocol):
    """Protocol for telemetry hooks.
    
    Implement this protocol to add custom observability to Halt.
    """
    
    def on_check(self, key: str, decision: Decision, metadata: Optional[dict] = None) -> None:
        """Called on every rate limit check.
        
        Args:
            key: Rate limit key
            decision: Rate limit decision
            metadata: Additional metadata (policy name, algorithm, etc.)
        """
        ...
    
    def on_allowed(self, key: str, decision: Decision, metadata: Optional[dict] = None) -> None:
        """Called when request is allowed.
        
        Args:
            key: Rate limit key
            decision: Rate limit decision
            metadata: Additional metadata
        """
        ...
    
    def on_blocked(self, key: str, decision: Decision, metadata: Optional[dict] = None) -> None:
        """Called when request is blocked.
        
        Args:
            key: Rate limit key
            decision: Rate limit decision
            metadata: Additional metadata
        """
        ...
    
    def on_quota_check(self, identifier: str, quota: Quota, allowed: bool) -> None:
        """Called when quota is checked.
        
        Args:
            identifier: User/key identifier
            quota: Quota configuration
            allowed: Whether quota allows the operation
        """
        ...
    
    def on_quota_exceeded(self, identifier: str, quota: Quota) -> None:
        """Called when quota is exceeded.
        
        Args:
            identifier: User/key identifier
            quota: Quota configuration
        """
        ...
    
    def on_penalty_applied(self, identifier: str, penalty: Penalty) -> None:
        """Called when penalty is applied.
        
        Args:
            identifier: User/key identifier
            penalty: Penalty state
        """
        ...
    
    def on_violation(self, identifier: str, penalty: Penalty, severity: float) -> None:
        """Called when violation is recorded.
        
        Args:
            identifier: User/key identifier
            penalty: Updated penalty state
            severity: Violation severity
        """
        ...


class LoggingTelemetry:
    """Simple logging-based telemetry implementation."""
    
    def __init__(self, logger: Any) -> None:
        """Initialize logging telemetry.
        
        Args:
            logger: Python logger instance
        """
        self.logger = logger
    
    def on_check(self, key: str, decision: Decision, metadata: Optional[dict] = None) -> None:
        """Log rate limit check."""
        self.logger.debug(
            f"Rate limit check: key={key}, allowed={decision.allowed}, "
            f"remaining={decision.remaining}, metadata={metadata}"
        )
    
    def on_allowed(self, key: str, decision: Decision, metadata: Optional[dict] = None) -> None:
        """Log allowed request."""
        self.logger.info(
            f"Request allowed: key={key}, remaining={decision.remaining}"
        )
    
    def on_blocked(self, key: str, decision: Decision, metadata: Optional[dict] = None) -> None:
        """Log blocked request."""
        self.logger.warning(
            f"Request blocked: key={key}, retry_after={decision.retry_after}s, "
            f"metadata={metadata}"
        )
    
    def on_quota_check(self, identifier: str, quota: Quota, allowed: bool) -> None:
        """Log quota check."""
        self.logger.debug(
            f"Quota check: identifier={identifier}, quota={quota.name}, "
            f"allowed={allowed}, remaining={quota.remaining()}"
        )
    
    def on_quota_exceeded(self, identifier: str, quota: Quota) -> None:
        """Log quota exceeded."""
        self.logger.warning(
            f"Quota exceeded: identifier={identifier}, quota={quota.name}, "
            f"limit={quota.limit}, reset_at={quota.reset_at}"
        )
    
    def on_penalty_applied(self, identifier: str, penalty: Penalty) -> None:
        """Log penalty applied."""
        self.logger.warning(
            f"Penalty applied: identifier={identifier}, "
            f"abuse_score={penalty.abuse_score}, "
            f"penalty_until={penalty.penalty_until}"
        )
    
    def on_violation(self, identifier: str, penalty: Penalty, severity: float) -> None:
        """Log violation."""
        self.logger.info(
            f"Violation recorded: identifier={identifier}, severity={severity}, "
            f"abuse_score={penalty.abuse_score}, violations={penalty.violations}"
        )


class MetricsTelemetry:
    """Metrics-based telemetry for Prometheus/StatsD."""
    
    def __init__(self, metrics_client: Any) -> None:
        """Initialize metrics telemetry.
        
        Args:
            metrics_client: Metrics client (Prometheus, StatsD, etc.)
        """
        self.metrics = metrics_client
    
    def on_check(self, key: str, decision: Decision, metadata: Optional[dict] = None) -> None:
        """Record rate limit check metric."""
        self.metrics.increment("halt.checks.total", tags=self._get_tags(metadata))
    
    def on_allowed(self, key: str, decision: Decision, metadata: Optional[dict] = None) -> None:
        """Record allowed request metric."""
        self.metrics.increment("halt.requests.allowed", tags=self._get_tags(metadata))
        self.metrics.gauge("halt.remaining", decision.remaining, tags=self._get_tags(metadata))
    
    def on_blocked(self, key: str, decision: Decision, metadata: Optional[dict] = None) -> None:
        """Record blocked request metric."""
        self.metrics.increment("halt.requests.blocked", tags=self._get_tags(metadata))
    
    def on_quota_check(self, identifier: str, quota: Quota, allowed: bool) -> None:
        """Record quota check metric."""
        tags = {"quota": quota.name, "period": quota.period.value}
        self.metrics.increment("halt.quota.checks", tags=tags)
        self.metrics.gauge("halt.quota.remaining", quota.remaining(), tags=tags)
    
    def on_quota_exceeded(self, identifier: str, quota: Quota) -> None:
        """Record quota exceeded metric."""
        tags = {"quota": quota.name, "period": quota.period.value}
        self.metrics.increment("halt.quota.exceeded", tags=tags)
    
    def on_penalty_applied(self, identifier: str, penalty: Penalty) -> None:
        """Record penalty applied metric."""
        self.metrics.increment("halt.penalties.applied")
        self.metrics.gauge("halt.penalties.abuse_score", penalty.abuse_score)
    
    def on_violation(self, identifier: str, penalty: Penalty, severity: float) -> None:
        """Record violation metric."""
        self.metrics.increment("halt.violations.total")
        self.metrics.histogram("halt.violations.severity", severity)
    
    def _get_tags(self, metadata: Optional[dict]) -> dict:
        """Extract tags from metadata."""
        if not metadata:
            return {}
        
        return {
            "policy": metadata.get("policy"),
            "algorithm": metadata.get("algorithm"),
        }


class CompositeTelemetry:
    """Combine multiple telemetry implementations."""
    
    def __init__(self, *hooks: TelemetryHooks) -> None:
        """Initialize composite telemetry.
        
        Args:
            *hooks: Telemetry hook implementations
        """
        self.hooks = hooks
    
    def on_check(self, key: str, decision: Decision, metadata: Optional[dict] = None) -> None:
        """Call on_check for all hooks."""
        for hook in self.hooks:
            hook.on_check(key, decision, metadata)
    
    def on_allowed(self, key: str, decision: Decision, metadata: Optional[dict] = None) -> None:
        """Call on_allowed for all hooks."""
        for hook in self.hooks:
            hook.on_allowed(key, decision, metadata)
    
    def on_blocked(self, key: str, decision: Decision, metadata: Optional[dict] = None) -> None:
        """Call on_blocked for all hooks."""
        for hook in self.hooks:
            hook.on_blocked(key, decision, metadata)
    
    def on_quota_check(self, identifier: str, quota: Quota, allowed: bool) -> None:
        """Call on_quota_check for all hooks."""
        for hook in self.hooks:
            hook.on_quota_check(identifier, quota, allowed)
    
    def on_quota_exceeded(self, identifier: str, quota: Quota) -> None:
        """Call on_quota_exceeded for all hooks."""
        for hook in self.hooks:
            hook.on_quota_exceeded(identifier, quota)
    
    def on_penalty_applied(self, identifier: str, penalty: Penalty) -> None:
        """Call on_penalty_applied for all hooks."""
        for hook in self.hooks:
            hook.on_penalty_applied(identifier, penalty)
    
    def on_violation(self, identifier: str, penalty: Penalty, severity: float) -> None:
        """Call on_violation for all hooks."""
        for hook in self.hooks:
            hook.on_violation(identifier, penalty, severity)
