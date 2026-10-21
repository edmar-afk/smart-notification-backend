
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
        
        
class PatientDoseHistoryListCreateView(APIView):
    permission_classes = [AllowAny]
    """
    GET: View all medicine history records.
    POST: Save a new medicine history record.
    """

    def get(self, request):
        queryset = PatientDoseHistory.objects.select_related(
            "patient"
        ).order_by("-id")

        patient_id = request.query_params.get("patient_id")

        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)

        serializer = PatientDoseHistorySerializer(
            queryset, many=True
        )
        return Response(serializer.data)

    def post(self, request):
        serializer = PatientDoseHistorySerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        patient_id = request.data.get("patient")

        if not patient_id:
            patient_id = request.data.get("patient_id")

        if not patient_id:
            return Response(
                {"patient": ["A patient ID is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            patient = UserProfile.objects.get(pk=patient_id)
        except (UserProfile.DoesNotExist, ValueError, TypeError):
            return Response(
                {"patient": ["The specified patient does not exist."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        history = serializer.save(patient=patient)

        return Response(
            PatientDoseHistorySerializer(history).data,
            status=status.HTTP_201_CREATED,
        )


class PatientDoseHistoryDetailView(APIView):
    permission_classes = [AllowAny]
    """
    GET: View history for one history-record ID.
    """

    def get(self, request, pk):
        try:
            history = PatientDoseHistory.objects.get(pk=pk)
        except PatientDoseHistory.DoesNotExist:
            return Response(
                {"detail": "Medicine history record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PatientDoseHistorySerializer(history)
        return Response(serializer.data)
