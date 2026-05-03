"""URL routes for the AutoSecAI prototype."""

from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html"), name="hyper3d"),
    path("api/", include("scanner.urls")),
]

urlpatterns += staticfiles_urlpatterns()

