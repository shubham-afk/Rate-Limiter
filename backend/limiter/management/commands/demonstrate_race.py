from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.core.management.base import BaseCommand
from django.conf import settings
from redis import Redis

from limiter.redis_limiter import RedisRateLimiter, UnsafeRedisFixedWindowLimiter


class Command(BaseCommand):
    help = "Demonstrate unsafe Redis read/check/write race, then the Lua fix."

    def handle(self, *args, **options):
        client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self._delete_demo_keys(client)
        barrier = Barrier(2)
        unsafe = UnsafeRedisFixedWindowLimiter(client, limit=1, window_seconds=60)
        with ThreadPoolExecutor(max_workers=2) as executor:
            unsafe_results = list(executor.map(lambda _: unsafe.check("race-demo", after_read=barrier.wait), range(2)))
        self.stdout.write(f"Unsafe GET/check/SET decisions (limit=1): {unsafe_results} — two requests allowed")
        self._delete_demo_keys(client)
        safe = RedisRateLimiter(client)
        with ThreadPoolExecutor(max_workers=2) as executor:
            safe_results = list(executor.map(lambda _: safe.check("race-demo", "fixed_window", 1, 60).allowed, range(2)))
        self.stdout.write(f"Atomic Lua decisions (limit=1): {safe_results} — exactly one request allowed")

    @staticmethod
    def _delete_demo_keys(client):
        """Clean up only this command's keys; never erase a shared Redis DB."""
        keys = list(client.scan_iter(match="rl:unsafe:race-demo:*"))
        keys.extend(client.scan_iter(match="rl:fixed:race-demo:*"))
        if keys:
            client.delete(*keys)
