from django.urls import path

from .views import LoginView, MeView, SignupView

urlpatterns = [
    path("auth/signup", SignupView.as_view(), name="signup"),
    path("auth/login", LoginView.as_view(), name="login"),
    path("users/me", MeView.as_view(), name="me"),
]
