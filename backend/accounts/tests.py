from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class AuthApiTests(APITestCase):
	def setUp(self):
		self.signup_url = reverse("signup")
		self.login_url = reverse("login")
		self.me_url = reverse("me")

	def test_signup_success(self):
		payload = {
			"name": "Yash",
			"email": "yash@example.com",
			"password": "StrongPass123",
		}

		response = self.client.post(self.signup_url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertTrue(User.objects.filter(email="yash@example.com").exists())
		self.assertIn("user", response.data)

	def test_signup_duplicate_email_fails(self):
		User.objects.create_user(
			name="Yash",
			email="yash@example.com",
			password="StrongPass123",
		)
		payload = {
			"name": "Yash 2",
			"email": "yash@example.com",
			"password": "AnotherPass123",
		}

		response = self.client.post(self.signup_url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("email", response.data)

	def test_login_success_returns_tokens(self):
		User.objects.create_user(
			name="Yash",
			email="yash@example.com",
			password="StrongPass123",
		)
		payload = {
			"email": "yash@example.com",
			"password": "StrongPass123",
		}

		response = self.client.post(self.login_url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn("access", response.data)
		self.assertIn("refresh", response.data)

	def test_login_invalid_credentials_fails(self):
		User.objects.create_user(
			name="Yash",
			email="yash@example.com",
			password="StrongPass123",
		)
		payload = {
			"email": "yash@example.com",
			"password": "WrongPass123",
		}

		response = self.client.post(self.login_url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_me_requires_authentication(self):
		response = self.client.get(self.me_url)
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_me_returns_current_user(self):
		user = User.objects.create_user(
			name="Yash",
			email="yash@example.com",
			password="StrongPass123",
		)
		login_response = self.client.post(
			self.login_url,
			{"email": "yash@example.com", "password": "StrongPass123"},
			format="json",
		)
		access_token = login_response.data["access"]
		self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

		response = self.client.get(self.me_url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["user_id"], user.user_id)
		self.assertEqual(response.data["email"], user.email)
