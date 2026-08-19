"""A small Redis queue that keeps PostgreSQL logging off the request path."""
from __future__ import annotations

import json
from typing import Any

from redis import Redis

EVENT_QUEUE_KEY = "rl:request-events"


class RequestEventPublisher:
    def __init__(self, client: Redis) -> None:
        self.client = client

    def publish(self, event: dict[str, Any]) -> None:
        # A Redis list preserves events until a background worker consumes them.
        self.client.rpush(EVENT_QUEUE_KEY, json.dumps(event))
