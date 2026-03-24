from django.urls import path

from .views import GroupSettlementListCreateView

urlpatterns = [
    path(
        "groups/<int:group_id>/settlements",
        GroupSettlementListCreateView.as_view(),
        name="group-settlements-list-create",
    ),
]
