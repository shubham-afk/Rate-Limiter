"""Authentication helpers for the operational API."""

from __future__ import annotations

from functools import wraps
from secrets import compare_digest

from django.conf import settings
from django.http import JsonResponse


def require_admin_token(view):
    """Require a configured bearer token before changing limiter rules."""
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        expected = settings.ADMIN_API_TOKEN
        if not expected:
            return JsonResponse({"detail": "Admin API is not configured."}, status=503)
        supplied = request.headers.get("Authorization", "")
        if not supplied.startswith("Bearer ") or not compare_digest(supplied[7:], expected):
            return JsonResponse({"detail": "Admin authentication is required."}, status=401)
        return view(request, *args, **kwargs)
    return wrapped
