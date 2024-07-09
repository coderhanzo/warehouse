from django.shortcuts import render
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status, generics, permissions
import requests
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication
from .serializers import UserSerializer, CreateUserSerializer
from djoser.serializers import SetPasswordRetypeSerializer
from djoser.compat import get_user_email
from .serializers import TokenRefreshSerializer
from django.contrib.auth import (
    authenticate,
    login,
    logout,
)
from django.template.loader import render_to_string
from django.contrib.auth.models import Permission
from django.utils.text import slugify

User = get_user_model()


# NEEDS TESTING
# Gets new access token else should return 401
# to get a new refresh token, login
@api_view(["GET"])
@permission_classes([AllowAny])
def refresh_token_view(request):
    # Access the refresh_token from the cookies sent with the request
    refresh_token = request.COOKIES.get("refresh_token")
    # if not refresh_token:
    #     return Response({"error": "Refresh token not found."}, status=400)

    # Prepare data for TokenRefreshView
    data = {"refresh": refresh_token}
    # Check simplejwt docs if this doesnt work
    serializer = TokenRefreshSerializer(data=data)
    try:
        serializer.is_valid(raise_exception=True)
    except TokenError:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    return Response(serializer.validated_data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    """Login view for local authentication"""
    email = request.data.get("email")
    password = request.data.get("password")

    user = authenticate(
        request,
        email=email,
        password=password,
    )

    if user and user.is_active:
        # If valid, issue JWT token
        token = RefreshToken().for_user(user)
        drf_response = Response(
            {
                "access": str(token.access_token),
            }
        )
        drf_response.set_cookie(
            key=settings.SIMPLE_JWT["AUTH_COOKIE"],
            value=str(token),
            httponly=True,
        )
        return drf_response
    return Response(
        {"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
    )


class GetUsers(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return User.objects.all()


def generate_unique_slug(model_class, title):
    """
    django-scheduler models aren't great but i'd rather not touch them/
    This function is here so that the slug field in the Calendar model is unique
    """
    original_slug = slugify(title)
    unique_slug = original_slug
    num = 1
    while model_class.objects.filter(slug=unique_slug).exists():
        unique_slug = "{}-{}".format(original_slug, num)
        num += 1
    return unique_slug


@api_view(["POST"])
@permission_classes([AllowAny])
@transaction.atomic
def signup_view(request):
    """Register view for local authentication"""
    user_data = {
        "first_name": request.data.get("first_name"),
        "last_name": request.data.get("last_name"),
        "email": request.data.get("email"),
        "password": request.data.get("password"),
        "phone_number": request.data.get("phone_number"),
        # Add other fields as needed
    }

    # if user_data.get("institution_admin"):
    #     institution_serializer = InstitutionSerializer(
    #         data={"name": user_data.get("institution_name")}
    #     )
    #     institution_serializer.is_valid(raise_exception=True)
    #     instituation_instance = institution_serializer.save()

    #     user_data["institution"] = instituation_instance.id

    # Post to app db
    serializer = CreateUserSerializer(data=user_data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()

    if user:
        # If account creation successful, issue JWT token
        token = RefreshToken().for_user(user)
        drf_response = Response(
            {
                "access": str(token.access_token),
            }
        )
        drf_response.set_cookie(
            key=settings.SIMPLE_JWT["AUTH_COOKIE"],
            value=str(token),
            httponly=True,
        )
        return drf_response
    return Response(
        {"detail": "Account creation failed"}, status=status.HTTP_400_BAD_REQUEST
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def get_logged_in_user(request):
    serializer = UserSerializer(instance=request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def logout(request):
    drf_response = Response(status=status.HTTP_200_OK)
    drf_response.delete_cookie(settings.SIMPLE_JWT["AUTH_COOKIE"])
    return drf_response


class SetPassword(APIView):
    def post(self, request):
        data = self.request.data
        print(data)
        serializer = SetPasswordRetypeSerializer(
            context={"request": self.request}, data=data
        )
        serializer.is_valid(raise_exception=True)

        self.request.user.set_password(serializer.data["new_password"])
        self.request.user.save()

        if settings.PASSWORD_CHANGED_EMAIL_CONFIRMATION:
            context = {"user": self.request.user}
            to = [get_user_email(self.request.user)]
            settings.EMAIL.password_changed_confirmation(self.request, context).send(to)

        if settings.LOGOUT_ON_PASSWORD_CHANGE:
            logout(self.request)
        elif settings.CREATE_SESSION_ON_LOGIN:
            update_session_auth_hash(self.request, self.request.user)
        return Response({"status": 200}, status=status.HTTP_200_OK)


@api_view(["POST"])
@transaction.atomic
def custom_password_reset_view(request):
    email = request.data.get("email")
    user = User.objects.filter(email=email).first()
    if not user:
        return Response(
            {"error": "User with this email does not exist."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Generate password reset token and UID
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    # Construct the password reset link (to be sent via email)
    reset_link = f"{settings.DOMAIN}/reset-password/{uid}/{token}/"

    # Send an email with the password reset link
    send_mail(
        subject="Password Reset for Your Adeeny Account",
        message=f"Please click the following link to reset your password: {reset_link}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )

    return Response({"message": "Password reset link sent."}, status=status.HTTP_200_OK)
