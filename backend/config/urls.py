from django.contrib import admin
from django.urls import path
from limiter import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", views.health),
    path("api/v1/keys/", views.rules),
    path("api/v1/keys/<int:rule_id>/", views.rule_detail),
    path("api/v1/analytics/", views.analytics),
    path("api/v1/events/", views.events),
    path("api/v1/compare/", views.compare),
    path("gateway/<path:upstream>", views.gateway),
]
