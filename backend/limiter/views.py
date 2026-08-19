import json
import logging
import secrets
from datetime import UTC, datetime

from django.db import DatabaseError, IntegrityError, transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from redis.exceptions import RedisError

from .models import ApiKey, RateLimitRule
from .auth import require_admin_token
from .redis_limiter import RedisRateLimiter, RuleStore

logger = logging.getLogger(__name__)


def health(request):
    return JsonResponse({"status": "ok"})


def data(request):
    """A deliberately small upstream stand-in protected by middleware."""
    return JsonResponse({"data": {"message": "Dummy protected response"}})


def _rule_payload(rule):
    return {"id": rule.id, "name": rule.name, "key": rule.api_key.key if rule.api_key else None, "tier": rule.api_key.tier if rule.api_key else None, "algorithm": rule.algorithm,
            "limit": rule.limit, "windowSeconds": rule.window_seconds, "scope": rule.scope,
            "endpoint": rule.endpoint or None, "createdAt": rule.created_at.isoformat(),
            "updatedAt": rule.updated_at.isoformat()}


def _body(request):
    try:
        return json.loads(request.body)
    except (ValueError, TypeError):
        return None


def _apply_rule(rule, data, creating=False):
    required = ["name", "limit", "windowSeconds", "algorithm"] if creating else ["limit", "windowSeconds", "algorithm"]
    if not data or any(field not in data for field in required):
        return "Missing required fields: " + ", ".join(required)
    if data["algorithm"] not in {choice for choice, _ in RateLimitRule.Algorithm.choices}:
        return "Unsupported algorithm."
    try:
        limit, window = int(data["limit"]), int(data["windowSeconds"])
        if limit < 1 or window < 1:
            raise ValueError
    except (TypeError, ValueError):
        return "limit and windowSeconds must be positive integers."
    if creating:
        rule.name = data["name"]
    rule.limit, rule.window_seconds, rule.algorithm = limit, window, data["algorithm"]
    rule.scope = data.get("scope", rule.scope or "api_key")
    if rule.scope not in {"api_key", "endpoint", "ip", "user"}:
        return "Unsupported scope."
    rule.endpoint = data.get("endpoint") or ""
    return None


@csrf_exempt
@require_http_methods(["POST"])
@require_admin_token
def keys(request):
    data = _body(request)
    api_key = ApiKey(name=(data or {}).get("name", ""), key=(data or {}).get("key") or secrets.token_urlsafe(24),
                     tier=(data or {}).get("tier", "free"))
    rule = RateLimitRule(api_key=api_key)
    error = _apply_rule(rule, data, creating=True)
    if error:
        return JsonResponse({"detail": error}, status=400)
    try:
        with transaction.atomic():
            api_key.save()
            rule.save()
    except IntegrityError:
        return JsonResponse({"detail": "API key already exists."}, status=409)
    return JsonResponse(_rule_payload(rule), status=201)


@csrf_exempt
@require_http_methods(["GET", "PUT"])
@require_admin_token
def key_detail(request, key):
    rule = RateLimitRule.objects.select_related("api_key").filter(api_key__key=key).first()
    if not rule:
        return JsonResponse({"detail": "API key not found."}, status=404)
    if request.method == "PUT":
        error = _apply_rule(rule, _body(request))
        if error:
            return JsonResponse({"detail": error}, status=400)
        rule.save()
        try:
            RuleStore(RedisRateLimiter().client).invalidate(key)
        except RedisError:  # Rule is safely stored; stale cache expires after five minutes.
            logger.warning("Could not invalidate Redis rule cache for key update", exc_info=True)
        return JsonResponse(_rule_payload(rule))
    return JsonResponse({"rule": _rule_payload(rule), "usage": "Usage snapshot arrives with Redis analytics in Phase 5."})


@csrf_exempt
@require_http_methods(["POST"])
def check(request):
    data = _body(request) or {}
    key, endpoint = data.get("key"), data.get("endpoint")
    if not key or not endpoint:
        return JsonResponse({"detail": "key and endpoint are required."}, status=400)
    try:
        store = RuleStore(RedisRateLimiter().client)
        rule = store.get_api_key_rule(key)
        if rule is None:
            return JsonResponse({"detail": "API key not found."}, status=404)
        identity = f"key:{key}:{endpoint}" if rule["scope"] == "endpoint" else f"key:{key}"
        result = RedisRateLimiter(store.client).check(identity, rule["algorithm"], rule["limit"], rule["window_seconds"])
    except (RedisError, DatabaseError, ValueError):
        logger.exception("Rate-limit check failed")
        return JsonResponse({"detail": "Rate limiter unavailable."}, status=503)
    return JsonResponse({"allowed": result.allowed, "remaining": result.remaining,
                         "resetAt": datetime.fromtimestamp(result.reset_at, UTC).isoformat()})


def metrics(request):
    return JsonResponse({"detail": "Live metrics are planned for Phase 5."}, status=501)


@csrf_exempt
@require_http_methods(["GET", "PUT"])
@require_admin_token
def ip_fallback_rule(request):
    rule = RateLimitRule.objects.filter(api_key__isnull=True, scope="ip").first()
    if request.method == "GET":
        if rule is None:
            return JsonResponse({"detail": "No IP fallback rule is configured."}, status=404)
        return JsonResponse(_rule_payload(rule))
    data = _body(request) or {}
    if rule is None:
        rule = RateLimitRule(name=data.get("name", "anonymous-ip-fallback"), scope="ip")
    creating = rule.pk is None
    error = _apply_rule(rule, {"name": data.get("name", rule.name), **data, "scope": "ip"}, creating=creating)
    if error:
        return JsonResponse({"detail": error}, status=400)
    rule.save()
    try:
        RuleStore(RedisRateLimiter().client).invalidate_fallback()
    except RedisError:
        logger.warning("Could not invalidate IP fallback rule cache", exc_info=True)
    return JsonResponse(_rule_payload(rule), status=201 if creating else 200)
