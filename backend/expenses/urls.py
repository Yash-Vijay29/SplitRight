from django.urls import path

from .views import GroupExpenseDetailView, GroupExpenseListCreateView

urlpatterns = [
    path(
        "groups/<int:group_id>/expenses",
        GroupExpenseListCreateView.as_view(),
        name="group-expenses-list-create",
    ),
    path(
        "groups/<int:group_id>/expenses/<int:expense_id>",
        GroupExpenseDetailView.as_view(),
        name="group-expenses-detail",
    ),
]