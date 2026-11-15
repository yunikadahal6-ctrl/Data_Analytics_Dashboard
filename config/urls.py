"""Top-level URL routes for the project."""

from django.urls import include, path


urlpatterns = [
    path("", include("dashboard.urls")),
]
