from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Group, GroupMember
from .serializers import GroupCreateSerializer, GroupMemberSerializer, GroupSerializer


def _ensure_group_member(user, group):
	is_member = GroupMember.objects.filter(user=user, group=group).exists()
	if not is_member:
		raise PermissionDenied("You are not a member of this group.")


class GroupListCreateView(APIView):
	def get(self, request):
		groups = (
			Group.objects.filter(memberships__user=request.user)
			.select_related("created_by")
			.order_by("-created_at")
			.distinct()
		)
		serializer = GroupSerializer(groups, many=True)
		return Response(
			{
				"count": len(serializer.data),
				"results": serializer.data,
			},
			status=status.HTTP_200_OK,
		)

	def post(self, request):
		serializer = GroupCreateSerializer(data=request.data, context={"request": request})
		serializer.is_valid(raise_exception=True)
		group = serializer.save()

		return Response(
			{
				"message": "Group created successfully.",
				"group": GroupSerializer(group).data,
			},
			status=status.HTTP_201_CREATED,
		)


class GroupDetailView(APIView):
	def get(self, request, group_id):
		group = get_object_or_404(Group.objects.select_related("created_by"), pk=group_id)
		_ensure_group_member(request.user, group)

		return Response(GroupSerializer(group).data, status=status.HTTP_200_OK)


class GroupJoinView(APIView):
	def post(self, request, group_id):
		group = get_object_or_404(Group, pk=group_id)

		if GroupMember.objects.filter(group=group, user=request.user).exists():
			return Response(
				{"message": "You are already a member of this group."},
				status=status.HTTP_400_BAD_REQUEST,
			)

		GroupMember.objects.create(group=group, user=request.user)
		return Response(
			{
				"message": "Joined group successfully.",
				"group": GroupSerializer(group).data,
			},
			status=status.HTTP_201_CREATED,
		)


class GroupMembersView(APIView):
	def get(self, request, group_id):
		group = get_object_or_404(Group.objects.select_related("created_by"), pk=group_id)
		_ensure_group_member(request.user, group)

		members = GroupMember.objects.filter(group=group).select_related("user").order_by("joined_at")
		members_serializer = GroupMemberSerializer(members, many=True)

		return Response(
			{
				"group": GroupSerializer(group).data,
				"count": len(members_serializer.data),
				"results": members_serializer.data,
			},
			status=status.HTTP_200_OK,
		)
