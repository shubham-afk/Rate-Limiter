from django.db import models


class ApiKey(models.Model):
    """A client credential, separate from its mutable limiting rule."""
    name = models.CharField(max_length=80)
    key = models.CharField(max_length=160, unique=True)
    tier = models.CharField(max_length=32, default="free")
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class RateLimitRule(models.Model):
    class Algorithm(models.TextChoices):
        FIXED = "fixed_window", "Fixed window"
        SLIDING_LOG = "sliding_window_log", "Sliding window log"
        TOKEN = "token_bucket", "Token bucket"
        SLIDING_COUNTER = "sliding_window_counter", "Sliding window counter"
    name = models.CharField(max_length=80)
    # Null identifies the one persisted fallback rule used for anonymous IPs.
    api_key = models.OneToOneField(ApiKey, null=True, blank=True, on_delete=models.CASCADE, related_name="rule")
    algorithm = models.CharField(max_length=32, choices=Algorithm.choices, default=Algorithm.FIXED)
    limit = models.PositiveIntegerField(default=60)
    window_seconds = models.PositiveIntegerField(default=60)
    scope = models.CharField(max_length=16, default="api_key")
    endpoint = models.CharField(max_length=200, blank=True)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class RequestLog(models.Model):
    """Written by the event worker, never synchronously in request middleware."""
    rule = models.ForeignKey(RateLimitRule, null=True, blank=True, on_delete=models.SET_NULL, related_name="events")
    key_label = models.CharField(max_length=160, blank=True)
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    endpoint = models.CharField(max_length=200)
    allowed = models.BooleanField()
    algorithm = models.CharField(max_length=32)
    latency_ms = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
