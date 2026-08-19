"""Redis-backed algorithms used by every Gatekeeper instance in Phase 2."""

from __future__ import annotations

import json
from dataclasses import dataclass
from time import time
from typing import Any

from django.conf import settings
from redis import Redis


@dataclass(frozen=True)
class LimitDecision:
    allowed: bool
    remaining: int
    reset_at: float


# Each script uses Redis TIME instead of a web-server clock, so instances with
# clock drift still make the same decision. EVAL executes the script atomically.
FIXED_WINDOW_LUA = """
local now = redis.call('TIME')
local second = tonumber(now[1])
local window = tonumber(ARGV[1])
local limit = tonumber(ARGV[2])
local bucket = math.floor(second / window)
local counter_key = KEYS[1] .. ':' .. bucket
local count = redis.call('INCR', counter_key)
if count == 1 then redis.call('EXPIRE', counter_key, window + 1) end
local reset = (bucket + 1) * window
if count > limit then return {0, 0, reset} end
return {1, limit - count, reset}
"""

TOKEN_BUCKET_LUA = """
local now_parts = redis.call('TIME')
local now = tonumber(now_parts[1]) + tonumber(now_parts[2]) / 1000000
local capacity = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local rate = capacity / window
local stored_tokens = tonumber(redis.call('HGET', KEYS[1], 'tokens'))
local previous = tonumber(redis.call('HGET', KEYS[1], 'updated_at'))
if not stored_tokens then stored_tokens = capacity end
if not previous then previous = now end
local tokens = math.min(capacity, stored_tokens + (now - previous) * rate)
local allowed = 0
if tokens >= 1 then tokens = tokens - 1; allowed = 1 end
redis.call('HSET', KEYS[1], 'tokens', tokens, 'updated_at', now)
redis.call('EXPIRE', KEYS[1], math.ceil(window * 2))
local reset = now + ((capacity - tokens) / rate)
return {allowed, math.floor(tokens), math.ceil(reset)}
"""

SLIDING_WINDOW_COUNTER_LUA = """
local now_parts = redis.call('TIME')
local second = tonumber(now_parts[1])
local window = tonumber(ARGV[1])
local limit = tonumber(ARGV[2])
local bucket = math.floor(second / window)
local elapsed = second - bucket * window
local current_key = KEYS[1] .. ':current:' .. bucket
local previous_key = KEYS[1] .. ':current:' .. (bucket - 1)
local current = tonumber(redis.call('GET', current_key)) or 0
local previous = tonumber(redis.call('GET', previous_key)) or 0
local effective = current + previous * ((window - elapsed) / window)
local reset = (bucket + 1) * window
if effective + 1 > limit then return {0, 0, reset} end
current = redis.call('INCR', current_key)
if current == 1 then redis.call('EXPIRE', current_key, window * 2 + 1) end
local remaining = math.max(0, math.floor(limit - (current + previous * ((window - elapsed) / window))))
return {1, remaining, reset}
"""


class RedisRateLimiter:
    def __init__(self, client: Redis | None = None) -> None:
        self.client = client or Redis.from_url(settings.REDIS_URL, decode_responses=True)

    def check(self, identity: str, algorithm: str, limit: int, window_seconds: int) -> LimitDecision:
        if algorithm == "fixed_window":
            result = self.client.eval(FIXED_WINDOW_LUA, 1, f"rl:fixed:{identity}", window_seconds, limit)
        elif algorithm == "token_bucket":
            result = self.client.eval(TOKEN_BUCKET_LUA, 1, f"rl:token:{identity}", limit, window_seconds)
        elif algorithm == "sliding_window_counter":
            result = self.client.eval(SLIDING_WINDOW_COUNTER_LUA, 1, f"rl:sliding:{identity}", window_seconds, limit)
        else:
            raise ValueError(f"Algorithm '{algorithm}' is not implemented in Phase 2")
        return LimitDecision(bool(int(result[0])), int(result[1]), float(result[2]))


class RuleStore:
    """Postgres is authoritative; Redis caches serialised rules between requests."""

    cache_ttl_seconds = 300

    def __init__(self, client: Redis) -> None:
        self.client = client

    def get_api_key_rule(self, key: str) -> dict[str, Any] | None:
        cache_key = f"rl:rule:{key}"
        cached = self.client.get(cache_key)
        if cached:
            return json.loads(cached)
        from .models import RateLimitRule

        rule = RateLimitRule.objects.select_related("api_key").filter(
            api_key__key=key, api_key__enabled=True, enabled=True
        ).first()
        if rule is None:
            return None
        payload = self._payload(rule)
        self.client.setex(cache_key, self.cache_ttl_seconds, json.dumps(payload))
        return payload

    def get_ip_fallback_rule(self) -> dict[str, Any] | None:
        cache_key = "rl:rule:fallback-ip"
        cached = self.client.get(cache_key)
        if cached:
            return json.loads(cached)
        from .models import RateLimitRule

        rule = RateLimitRule.objects.filter(api_key__isnull=True, scope="ip", enabled=True).first()
        if rule is None:
            return None
        payload = self._payload(rule)
        self.client.setex(cache_key, self.cache_ttl_seconds, json.dumps(payload))
        return payload

    @staticmethod
    def _payload(rule) -> dict[str, Any]:
        return {"rule_id": rule.id, "algorithm": rule.algorithm, "limit": rule.limit,
                "window_seconds": rule.window_seconds, "scope": rule.scope, "endpoint": rule.endpoint}

    def invalidate(self, key: str) -> None:
        self.client.delete(f"rl:rule:{key}")

    def invalidate_fallback(self) -> None:
        self.client.delete("rl:rule:fallback-ip")


class UnsafeRedisFixedWindowLimiter:
    """Educational anti-pattern: separate GET/SET calls are not atomic.

    This class is never wired into request middleware. The race demo/test uses
    it to show why the Lua implementations above exist.
    """

    def __init__(self, client: Redis, limit: int, window_seconds: int) -> None:
        self.client, self.limit, self.window_seconds = client, limit, window_seconds

    def check(self, identity: str, after_read=None) -> bool:
        bucket = int(time() // self.window_seconds)
        key = f"rl:unsafe:{identity}:{bucket}"
        count = int(self.client.get(key) or 0)
        if after_read:
            after_read()
        if count >= self.limit:
            return False
        # Two workers can both read zero and each write one: both return true.
        self.client.set(key, count + 1, ex=self.window_seconds + 1)
        return True
