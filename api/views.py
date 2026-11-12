
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import viewsets
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.db import transaction
from .models import UserProfile, PatientDose, Reminders, PatientDoseHistory
from .serializers import (
    UserProfileSerializer, PatientDoseHistorySerializer,
    RegisterSerializer, PatientDoseSerializer, RemindersSerializer
)
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        user = self.user

        data["user"] = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
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



class PatientListView(generics.ListAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return (
            UserProfile.objects.filter(
                user__is_superuser=False,
                user__is_staff=False,
            )
            .select_related("user")
            .order_by("id")
        )


class StudentReminderView(generics.GenericAPIView):
    serializer_class = RemindersSerializer
    permission_classes = [AllowAny]

    def get(self, request):
        reminder = Reminders.objects.filter(
            user=request.user
        ).first()

        if reminder is None:
            return Response({
                "exists": False,
                "notification_type": None,
            })

        return Response({
            "exists": True,
            **RemindersSerializer(reminder).data,
        })

    @transaction.atomic
    def post(self, request):
        reminder = Reminders.objects.filter(
            user=request.user
        ).first()

        serializer = self.get_serializer(
            reminder,
            data=request.data,
            partial=reminder is not None,
        )
        serializer.is_valid(raise_exception=True)

        serializer.save(user=request.user)

        return Response({
            "message": (
                "Reminder updated."
                if reminder is not None
                else "Reminder created."
            ),
            "reminder": serializer.data,
        })


class PatientDoseViewSet(viewsets.ModelViewSet):
    queryset = PatientDose.objects.select_related(
        "patient",
        "patient__user",
    ).all().order_by("-id")

    serializer_class = PatientDoseSerializer
    permission_classes = [AllowAny]
    
    
class PatientDoseListView(generics.ListAPIView):
    serializer_class = PatientDoseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.kwargs["user_id"]

        return (
            PatientDose.objects
            .select_related("patient", "patient__user")
            .filter(patient__user_id=user_id)
            .order_by("-id")
        )
        
        
User = get_user_model()



class PatientDoseHistoryListCreateView(APIView):
    permission_classes = [AllowAny]

    """
    GET: Retrieve medicine history for one Django user.
    POST: Save medicine history for one Django user.

    PatientDoseHistory.patient references django.contrib.auth.models.User.
    Therefore, use patient_id=user_id, not patient__user_id.
    """

    def get(self, request, user_id):
        print("========== DOSE HISTORY GET ==========")
        print("Django User ID:", user_id)

        get_object_or_404(User, pk=user_id)

        queryset = PatientDoseHistory.objects.filter(
            patient_id=user_id
        ).order_by("-id")

        serializer = PatientDoseHistorySerializer(
            queryset,
            many=True
        )

        print("History records found:", len(serializer.data))
        print("======================================")

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @transaction.atomic
    def post(self, request, user_id):
        print("========== DOSE HISTORY POST ==========")
        print("Django User ID:", user_id)
        print("Request data:", request.data)

        user = get_object_or_404(User, pk=user_id)

        payload = request.data.copy()

        # Always assign the user from the URL.
        # Do not trust a patient ID supplied by the client.
        payload["patient"] = user.pk

        serializer = PatientDoseHistorySerializer(data=payload)

        if not serializer.is_valid():
            print("Serializer errors:", serializer.errors)

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        history = serializer.save(patient=user)

        print("Saved history ID:", history.pk)
        print("Saved Django User ID:", user.pk)
        print("=======================================")

        return Response(
            PatientDoseHistorySerializer(history).data,
            status=status.HTTP_201_CREATED
        )


class PatientDoseHistoryDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id, pk):
        get_object_or_404(User, pk=user_id)

        history = get_object_or_404(
            PatientDoseHistory,
            pk=pk,
            patient_id=user_id
        )

        serializer = PatientDoseHistorySerializer(history)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )
