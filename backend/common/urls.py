from django.urls import path

from .views import FrontendAppView

urlpatterns = [
    path("", FrontendAppView.as_view(), name="frontend-app"),
]
