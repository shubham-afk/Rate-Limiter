from django.contrib import admin
from django.urls import path
from limiter import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", views.health),
    path("api/data", views.data),
]
