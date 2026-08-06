from django.db import models

class RateLimitRule(models.Model):
    class Algorithm(models.TextChoices):
        FIXED = "fixed_window", "Fixed window"
        SLIDING_LOG = "sliding_log", "Sliding window log"
        TOKEN = "token_bucket", "Token bucket"
        SLIDING_COUNTER = "sliding_counter", "Sliding window counter"
    name = models.CharField(max_length=80)
    key = models.CharField(max_length=160, unique=True)
    algorithm = models.CharField(max_length=32, choices=Algorithm.choices, default=Algorithm.TOKEN)
    limit = models.PositiveIntegerField(default=60)
    window_seconds = models.PositiveIntegerField(default=60)
    scope = models.CharField(max_length=16, default="api_key")
    endpoint = models.CharField(max_length=200, blank=True)
    tier = models.CharField(max_length=32, default="free")
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class RequestEvent(models.Model):
    rule = models.ForeignKey(RateLimitRule, null=True, blank=True, on_delete=models.SET_NULL, related_name="events")
    key_label = models.CharField(max_length=160)
    endpoint = models.CharField(max_length=200)
    allowed = models.BooleanField()
    algorithm = models.CharField(max_length=32)
    latency_ms = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
