"""Middleware that protects the Phase 1 dummy endpoint."""

from __future__ import annotations

from datetime import UTC, datetime

from django.conf import settings
from django.http import JsonResponse

from .fixed_window import FixedWindowLimiter


_limiter = FixedWindowLimiter(
    limit=settings.RATE_LIMIT_LIMIT,
    window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
)


def set_limiter_for_testing(limiter: FixedWindowLimiter) -> None:
    """Replace the process-global limiter in Django integration tests only."""
    global _limiter
    _limiter = limiter


class FixedWindowRateLimitMiddleware:
    """Enforce an in-memory fixed-window quota before `/api/data` runs."""

    protected_path = "/api/data"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path != self.protected_path:
            return self.get_response(request)

        # Phase 1 scopes counters by the supplied API-key header. Key issuance
        # and persistent rule lookup arrive in later phases, but the protected
        # endpoint already requires callers to identify themselves.
        identity = request.headers.get("X-API-Key")
        if not identity:
            return JsonResponse({"detail": "X-API-Key header is required."}, status=401)
        decision = _limiter.check(identity)
        request.rate_limit_decision = decision

        if not decision.allowed:
            retry_after = max(0, int(decision.reset_at - datetime.now(UTC).timestamp()))
            response = JsonResponse(
                {
                    "detail": "Rate limit exceeded.",
                    "remaining": decision.remaining,
                    "resetAt": datetime.fromtimestamp(decision.reset_at, UTC).isoformat(),
                },
                status=429,
            )
            response["Retry-After"] = str(retry_after)
            return response

        response = self.get_response(request)
        response["X-RateLimit-Limit"] = str(_limiter.limit)
        response["X-RateLimit-Remaining"] = str(decision.remaining)
        response["X-RateLimit-Reset"] = str(int(decision.reset_at))
        return response
