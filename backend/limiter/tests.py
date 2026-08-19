from django.test import TestCase, override_settings

from .fixed_window import FixedWindowLimiter
from .event_queue import RequestEventPublisher
from .redis_limiter import RedisRateLimiter


class FixedWindowLimiterTests(TestCase):
    def test_rejects_request_after_quota_in_the_same_window(self):
        limiter = FixedWindowLimiter(limit=2, window_seconds=60, clock=lambda: 10)

        self.assertTrue(limiter.check("demo-key").allowed)
        self.assertTrue(limiter.check("demo-key").allowed)
        denied = limiter.check("demo-key")

        self.assertFalse(denied.allowed)
        self.assertEqual(denied.remaining, 0)
        self.assertEqual(denied.reset_at, 60)

    def test_boundary_burst_flaw_allows_two_full_quotas_in_two_seconds(self):
        """Document fixed-window's known burst-at-boundary trade-off.

        100 calls at 00:00:59 and 100 more at 00:01:01 all pass, despite a
        nominal 100 requests/minute limit. This is intentional evidence for
        why Phase 3 will offer sliding and token-bucket algorithms.
        """
        current_time = 59.0
        limiter = FixedWindowLimiter(limit=100, window_seconds=60, clock=lambda: current_time)

        before_boundary = [limiter.check("demo-key") for _ in range(100)]
        current_time = 61.0
        after_boundary = [limiter.check("demo-key") for _ in range(100)]

        self.assertTrue(all(decision.allowed for decision in before_boundary))
        self.assertTrue(all(decision.allowed for decision in after_boundary))
        self.assertFalse(limiter.check("demo-key").allowed)


class RecordingRedis:
    def __init__(self):
        self.calls = []

    def eval(self, script, key_count, *args):
        self.calls.append((script, key_count, args))
        return [1, 7, 123]

    def rpush(self, key, payload):
        self.calls.append(("rpush", key, payload))


class RedisAlgorithmDispatchTests(TestCase):
    def test_dispatches_algorithms_to_atomic_lua_script(self):
        client = RecordingRedis()
        limiter = RedisRateLimiter(client)

        decision = limiter.check("demo-key", "token_bucket", 10, 60)

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.remaining, 7)
        self.assertEqual(client.calls[0][1], 1)
        self.assertEqual(client.calls[0][2], ("rl:token:demo-key", 10, 60))

    def test_uses_the_sliding_window_counter_script_for_its_rule_identifier(self):
        client = RecordingRedis()

        RedisRateLimiter(client).check("demo-key", "sliding_window_counter", 10, 60)

        self.assertEqual(client.calls[0][2], ("rl:sliding:demo-key", 60, 10))


@override_settings(ADMIN_API_TOKEN="test-admin-token")
class AdminRuleApiTests(TestCase):
    payload = {"name": "demo", "key": "demo-key", "algorithm": "sliding_window_counter", "limit": 10, "windowSeconds": 60}

    def test_admin_api_requires_bearer_token(self):
        response = self.client.post("/admin/keys", self.payload, content_type="application/json")

        self.assertEqual(response.status_code, 401)

    def test_admin_api_creates_a_supported_sliding_counter_rule(self):
        response = self.client.post("/admin/keys", self.payload, content_type="application/json",
                                    HTTP_AUTHORIZATION="Bearer test-admin-token")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["algorithm"], "sliding_window_counter")

    def test_ip_fallback_rule_is_persisted_without_an_api_key(self):
        payload = {"name": "anonymous", "algorithm": "fixed_window", "limit": 5, "windowSeconds": 60}

        response = self.client.put("/admin/rules/ip-fallback", payload, content_type="application/json",
                                   HTTP_AUTHORIZATION="Bearer test-admin-token")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["scope"], "ip")
        self.assertIsNone(response.json()["key"])


class RequestEventQueueTests(TestCase):
    def test_event_is_enqueued_without_database_write(self):
        client = RecordingRedis()

        RequestEventPublisher(client).publish({"allowed": True, "endpoint": "/api/data"})

        self.assertEqual(client.calls[0][0], "rpush")
