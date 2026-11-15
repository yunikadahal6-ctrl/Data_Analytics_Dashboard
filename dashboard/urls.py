"""URL routes owned by the dashboard app."""

from django.urls import path

from . import views


app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("upload/", views.upload_sales, name="upload_sales"),
    path("sql-practice/", views.sql_practice, name="sql_practice"),
]
