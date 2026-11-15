
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import (
    UserProfile,
    PatientDose,
    Reminders,
    PatientDoseHistory,
)

from .serializers import (
    UserProfileSerializer,
    PatientDoseHistorySerializer,
    RegisterSerializer,
    PatientDoseSerializer,
    RemindersSerializer,
)


User = get_user_model()


# ============================================================
# JWT LOGIN
# ============================================================

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


# ============================================================
# REGISTRATION
# ============================================================

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


# ============================================================
# LOGIN
# ============================================================

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

        profile, _ = UserProfile.objects.get_or_create(
            user=user
        )

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


# ============================================================
# USER PROFILE
# ============================================================

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        profile, _ = UserProfile.objects.get_or_create(
            user=self.request.user
        )
        return profile


# ============================================================
# PATIENT LIST
# ============================================================

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


# ============================================================
# PATIENT DOSE LIST AND CREATE
# ============================================================

class PatientDoseListCreateView(generics.ListCreateAPIView):
    serializer_class = PatientDoseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = PatientDose.objects.select_related(
            "patient",
            "patient__user",
        ).order_by("-id")

        is_deleted = self.request.query_params.get(
            "is_deleted", "false"
        )

        if is_deleted == "true":
            queryset = queryset.filter(is_deleted=True)

        elif is_deleted == "all":
            pass

        else:
            queryset = queryset.filter(is_deleted=False)

        patient_id = self.request.query_params.get("patient")

        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)

        return queryset

    def perform_create(self, serializer):
        user_id = self.request.data.get("user_id")

        if not user_id:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({
                "user_id": "User ID is required."
            })

        user = get_object_or_404(User, pk=user_id)

        profile, created = UserProfile.objects.get_or_create(
            user=user
        )

        serializer.save(
            patient=profile,
            is_deleted=False,
            deleted_at=None,
        )


# ============================================================
# PATIENT DOSE DETAIL / SOFT DELETE
# ============================================================

class PatientDoseDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PatientDoseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return PatientDose.objects.select_related(
            "patient",
            "patient__user",
        ).filter(is_deleted=False)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.deleted_at = timezone.now()

        instance.save(update_fields=[
            "is_deleted",
            "deleted_at",
        ])


# ============================================================
# PATIENT DOSE RESTORE
# ============================================================

class RestorePatientDoseView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, pk):
        dose = get_object_or_404(
            PatientDose,
            pk=pk,
            is_deleted=True,
        )

        dose.is_deleted = False
        dose.deleted_at = None

        dose.save(update_fields=[
            "is_deleted",
            "deleted_at",
        ])

        return Response({
            "message": "Patient dose restored successfully.",
            "id": dose.id,
            "is_deleted": False,
        }, status=status.HTTP_200_OK)


# ============================================================
# PATIENT DOSES BY USER
# ============================================================

class PatientDoseListView(generics.ListAPIView):
    serializer_class = PatientDoseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.kwargs["user_id"]

        queryset = (
            PatientDose.objects
            .select_related("patient", "patient__user")
            .filter(patient__user_id=user_id)
        )

        is_deleted = self.request.query_params.get(
            "is_deleted", "false"
        )

        if is_deleted == "true":
            queryset = queryset.filter(is_deleted=True)

        elif is_deleted == "all":
            pass

        else:
            queryset = queryset.filter(is_deleted=False)

        return queryset.order_by("-id")


# ============================================================
# OPTIONAL PATIENT DOSE VIEWSET
# Use this if you have registered PatientDoseViewSet
# with a DRF router.
# ============================================================

class PatientDoseViewSet(viewsets.ModelViewSet):
    serializer_class = PatientDoseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = PatientDose.objects.select_related(
            "patient",
            "patient__user",
        )

        if getattr(self, "action", None) == "restore":
            return queryset.filter(is_deleted=True)

        is_deleted = self.request.query_params.get(
            "is_deleted", "false"
        )

        if is_deleted == "true":
            return queryset.filter(is_deleted=True)

        if is_deleted == "all":
            return queryset.order_by("-id")

        return queryset.filter(
            is_deleted=False
        ).order_by("-id")

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.deleted_at = timezone.now()

        instance.save(update_fields=[
            "is_deleted",
            "deleted_at",
        ])

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        dose = self.get_object()

        dose.is_deleted = False
        dose.deleted_at = None

        dose.save(update_fields=[
            "is_deleted",
            "deleted_at",
        ])

        return Response({
            "message": "Patient dose restored successfully.",
            "id": dose.id,
            "is_deleted": False,
        })


# ============================================================
# STUDENT REMINDERS
# ============================================================

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


# ============================================================
# PATIENT DOSE HISTORY LIST / CREATE
# ============================================================

class PatientDoseHistoryListCreateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        get_object_or_404(User, pk=user_id)

        is_deleted = request.query_params.get(
            "is_deleted", "false"
        )

        queryset = PatientDoseHistory.objects.filter(
            patient_id=user_id
        )

        if is_deleted == "true":
            queryset = queryset.filter(is_deleted=True)

        elif is_deleted == "all":
            pass

        else:
            queryset = queryset.filter(is_deleted=False)

        queryset = queryset.order_by("-id")

        serializer = PatientDoseHistorySerializer(
            queryset,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @transaction.atomic
    def post(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)

        payload = request.data.copy()
        payload["patient"] = user.pk

        serializer = PatientDoseHistorySerializer(
            data=payload
        )

        serializer.is_valid(raise_exception=True)

        history = serializer.save(
            patient=user,
            is_deleted=False,
            deleted_at=None,
        )

        return Response(
            PatientDoseHistorySerializer(history).data,
            status=status.HTTP_201_CREATED
        )


# ============================================================
# PATIENT DOSE HISTORY DETAIL / SOFT DELETE
# ============================================================

class PatientDoseHistoryDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id, pk):
        get_object_or_404(User, pk=user_id)

        history = get_object_or_404(
            PatientDoseHistory,
            pk=pk,
            patient_id=user_id,
            is_deleted=False,
        )

        serializer = PatientDoseHistorySerializer(history)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def delete(self, request, user_id, pk):
        get_object_or_404(User, pk=user_id)

        history = get_object_or_404(
            PatientDoseHistory,
            pk=pk,
            patient_id=user_id,
            is_deleted=False,
        )

        history.is_deleted = True
        history.deleted_at = timezone.now()

        history.save(update_fields=[
            "is_deleted",
            "deleted_at",
        ])

        return Response({
            "message": "Dose history moved to recycle bin.",
            "id": history.id,
            "is_deleted": True,
        }, status=status.HTTP_200_OK)


# ============================================================
# PATIENT DOSE HISTORY RESTORE
# ============================================================

class RestorePatientDoseHistoryView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, user_id, pk):
        get_object_or_404(User, pk=user_id)

        history = get_object_or_404(
            PatientDoseHistory,
            pk=pk,
            patient_id=user_id,
            is_deleted=True,
        )

        history.is_deleted = False
        history.deleted_at = None

        history.save(update_fields=[
            "is_deleted",
            "deleted_at",
        ])

        return Response({
            "message": "Dose history restored successfully.",
            "id": history.id,
            "is_deleted": False,
        }, status=status.HTTP_200_OK)
