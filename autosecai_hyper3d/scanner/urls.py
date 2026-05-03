from django.urls import path

from .views import health, scan_code

urlpatterns = [
    path("health/", health, name="health"),
    path("scan/", scan_code, name="scan-code"),
]

