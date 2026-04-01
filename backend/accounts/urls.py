from django.urls import path

from .views import LoginView, MeView, SignupView, UserSearchView

urlpatterns = [
    path("auth/signup", SignupView.as_view(), name="signup"),
    path("auth/login", LoginView.as_view(), name="login"),
    path("users/me", MeView.as_view(), name="me"),
    path("users/search", UserSearchView.as_view(), name="users-search"),
]
