from django.contrib import admin
from django.urls import path
from limiter import views

urlpatterns = [
    path("admin/keys", views.keys),
    path("admin/keys/<str:key>", views.key_detail),
    path("admin/rules/ip-fallback", views.ip_fallback_rule),
    path("admin/", admin.site.urls),
    path("health/", views.health),
    path("check", views.check),
    path("api/data", views.data),
    path("metrics", views.metrics),
]
