from django.contrib import admin
from .models import ApiKey, RateLimitRule, RequestLog

admin.site.register(ApiKey)
admin.site.register(RateLimitRule)
admin.site.register(RequestLog)
