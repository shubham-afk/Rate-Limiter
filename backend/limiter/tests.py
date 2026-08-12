from django.test import TestCase

from .fixed_window import FixedWindowLimiter
from .middleware import set_limiter_for_testing


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


class ProtectedEndpointTests(TestCase):
    def setUp(self):
        self.limiter = FixedWindowLimiter(limit=2, window_seconds=60, clock=lambda: 10)
        set_limiter_for_testing(self.limiter)

    def tearDown(self):
        # Restore the normal development configuration for following tests.
        from django.conf import settings

        set_limiter_for_testing(
            FixedWindowLimiter(settings.RATE_LIMIT_LIMIT, settings.RATE_LIMIT_WINDOW_SECONDS)
        )

    def test_data_endpoint_returns_429_after_the_limit(self):
        headers = {"HTTP_X_API_KEY": "demo-key"}

        self.assertEqual(self.client.get("/api/data", **headers).status_code, 200)
        allowed = self.client.get("/api/data", **headers)
        denied = self.client.get("/api/data", **headers)

        self.assertEqual(allowed["X-RateLimit-Remaining"], "0")
        self.assertEqual(denied.status_code, 429)
        self.assertEqual(denied.json()["remaining"], 0)

    def test_data_endpoint_requires_an_api_key(self):
        response = self.client.get("/api/data")

        self.assertEqual(response.status_code, 401)
