"""Redis-backed gateway middleware."""
from datetime import UTC, datetime
import logging

from django.db import DatabaseError
from django.http import JsonResponse
from redis.exceptions import RedisError

from .redis_limiter import RedisRateLimiter, RuleStore
from .event_queue import RequestEventPublisher

logger = logging.getLogger(__name__)

class RedisRateLimitMiddleware:
    protected_path = "/api/data"

    def __init__(self, get_response):
        self.get_response = get_response
        self.limiter = RedisRateLimiter()
        self.rules = RuleStore(self.limiter.client)
        self.events = RequestEventPublisher(self.limiter.client)

    def __call__(self, request):
        if request.path != self.protected_path:
            return self.get_response(request)
        key = request.headers.get("X-API-Key")
        client_ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "")).split(",")[0].strip()
        started = datetime.now(UTC)
        try:
            if key:
                rule = self.rules.get_api_key_rule(key)
                identity = f"key:{key}"
            else:
                rule = self.rules.get_ip_fallback_rule()
                identity = f"ip:{client_ip}"
            if rule is None:
                return JsonResponse({"detail": "Unknown API key or no IP fallback rule is configured."}, status=401)
            if rule["endpoint"] and rule["endpoint"] != request.path:
                return JsonResponse({"detail": "API key is not valid for this endpoint."}, status=403)
            if rule["scope"] == "endpoint":
                identity = f"{identity}:{request.path}"
            decision = self.limiter.check(identity, rule["algorithm"], rule["limit"], rule["window_seconds"])
        except (RedisError, DatabaseError, ValueError):
            # Fail closed: avoid exposing the protected API if distributed state is unavailable.
            logger.exception("Rate-limit decision failed")
            return JsonResponse({"detail": "Rate limiter unavailable."}, status=503)
        reset_at = datetime.fromtimestamp(decision.reset_at, UTC).isoformat()
        self._publish_event(rule, key, client_ip, request.path, decision.allowed, started)
        if not decision.allowed:
            retry_after = max(0, int(decision.reset_at - datetime.now(UTC).timestamp()))
            response = JsonResponse({"detail": "Rate limit exceeded.", "remaining": 0, "resetAt": reset_at}, status=429)
            response["Retry-After"] = str(retry_after)
            return response
        response = self.get_response(request)
        response["X-RateLimit-Limit"] = str(rule["limit"])
        response["X-RateLimit-Remaining"] = str(decision.remaining)
        response["X-RateLimit-Reset"] = str(int(decision.reset_at))
        return response

    def _publish_event(self, rule, key, client_ip, endpoint, allowed, started):
        """Logging failure must not change an already-made rate-limit decision."""
        try:
            elapsed = (datetime.now(UTC) - started).total_seconds() * 1000
            self.events.publish({"rule_id": rule["rule_id"], "key_label": key or "",
                                 "client_ip": client_ip or None, "endpoint": endpoint,
                                 "allowed": allowed, "algorithm": rule["algorithm"], "latency_ms": elapsed})
        except RedisError:
            logger.warning("Could not enqueue request event", exc_info=True)
