from django.urls import path

from .views import GroupDetailView, GroupJoinView, GroupListCreateView, GroupMembersView

urlpatterns = [
    path("groups", GroupListCreateView.as_view(), name="groups-list-create"),
    path("groups/<int:group_id>", GroupDetailView.as_view(), name="groups-detail"),
    path("groups/<int:group_id>/join", GroupJoinView.as_view(), name="groups-join"),
    path("groups/<int:group_id>/members", GroupMembersView.as_view(), name="groups-members"),
]
