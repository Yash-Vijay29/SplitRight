from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import LoginSerializer, SignupSerializer, UserLookupSerializer, UserSerializer


class SignupView(APIView):
	permission_classes = [AllowAny]

	def post(self, request):
		serializer = SignupSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		user = serializer.save()
		return Response(
			{
				"message": "Signup successful.",
				"user": UserSerializer(user).data,
			},
			status=status.HTTP_201_CREATED,
		)


class LoginView(APIView):
	permission_classes = [AllowAny]

	def post(self, request):
		serializer = LoginSerializer(data=request.data, context={"request": request})
		serializer.is_valid(raise_exception=True)
		user = serializer.validated_data["user"]

		refresh = RefreshToken.for_user(user)
		return Response(
			{
				"message": "Login successful.",
				"access": str(refresh.access_token),
				"refresh": str(refresh),
				"user": UserSerializer(user).data,
			},
			status=status.HTTP_200_OK,
		)


class MeView(APIView):
	def get(self, request):
		return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)


class UserSearchView(APIView):
	def get(self, request):
		query = request.query_params.get("q", "").strip()

		try:
			limit = int(request.query_params.get("limit", 20))
		except (TypeError, ValueError):
			limit = 20

		limit = max(1, min(limit, 100))

		if len(query) < 2:
			return Response(
				{
					"count": 0,
					"results": [],
				},
				status=status.HTTP_200_OK,
			)

		users = (
			User.objects.filter(Q(name__icontains=query) | Q(email__icontains=query))
			.order_by("name", "email")[:limit]
		)
		serializer = UserLookupSerializer(users, many=True)

		return Response(
			{
				"count": len(serializer.data),
				"results": serializer.data,
			},
			status=status.HTTP_200_OK,
		)
