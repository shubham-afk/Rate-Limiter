"""Run the asynchronous Redis-to-PostgreSQL request-log writer."""
from __future__ import annotations

import json
import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import DatabaseError
from redis import Redis
from redis.exceptions import RedisError

from limiter.event_queue import EVENT_QUEUE_KEY
from limiter.models import RequestLog

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Continuously persist queued rate-limit events to PostgreSQL."

    def handle(self, *args, **options):
        client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.stdout.write("Request-event worker started")
        while True:
            try:
                item = client.blpop(EVENT_QUEUE_KEY, timeout=5)
                if item is None:
                    continue
                _, raw_event = item
                event = json.loads(raw_event)
                RequestLog.objects.create(**event)
            except DatabaseError:
                # Redis is the durable hand-off while Postgres is unavailable.
                logger.exception("Could not persist request event; returning it to the queue")
                try:
                    client.rpush(EVENT_QUEUE_KEY, raw_event)
                except RedisError:
                    logger.exception("Could not return request event to Redis")
            except (RedisError, ValueError, TypeError):
                logger.exception("Could not consume request event")
