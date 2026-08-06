from django.contrib import admin
from .models import RateLimitRule, RequestEvent
admin.site.register(RateLimitRule)
admin.site.register(RequestEvent)
