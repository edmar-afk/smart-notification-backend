
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token

from .models import UserProfile, PatientDose
from .serializers import (
    UserProfileSerializer,
    RegisterSerializer, PatientDoseSerializer
)


from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        if not self.user.is_superuser:
            raise AuthenticationFailed(
                "Access denied. Only administrators can log in."
            )

        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "is_superuser": self.user.is_superuser,
        }

        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"error": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is None:
            return Response(
                {"error": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        token, created = Token.objects.get_or_create(user=user)

        profile, _ = UserProfile.objects.get_or_create(user=user)

        return Response({
            "message": "Login successful.",
            "token": token.key,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            "profile": UserProfileSerializer(profile).data,
        })


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        profile, _ = UserProfile.objects.get_or_create(
            user=self.request.user
        )
        return profile


class PatientListView(generics.ListAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return UserProfile.objects.filter(
            user__is_superuser=False,
            user__is_staff=False,
        ).select_related("user").order_by("id")
        
        

class PatientDoseListCreateView(generics.ListCreateAPIView):
    serializer_class = PatientDoseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = PatientDose.objects.select_related(
            "patient",
            "patient__user",
        ).order_by("-id")

        patient_id = self.request.query_params.get("patient")

        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)

        return queryset


class PatientDoseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PatientDose.objects.select_related(
        "patient",
        "patient__user",
    ).all()
    serializer_class = PatientDoseSerializer
    permission_classes = [AllowAny]
