from django.urls import path

from .views import GroupBalancesView, GroupPairwiseBalancesView, MyBalancesView

urlpatterns = [
    path(
        "groups/<int:group_id>/balances",
        GroupBalancesView.as_view(),
        name="group-balances",
    ),
    path(
        "groups/<int:group_id>/balances/pairwise",
        GroupPairwiseBalancesView.as_view(),
        name="group-balances-pairwise",
    ),
    path(
        "users/me/balances",
        MyBalancesView.as_view(),
        name="me-balances",
    ),
]
