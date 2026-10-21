
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers

from .models import UserProfile, PatientDose, Reminders, PatientDoseHistory


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source="user.username",
        read_only=True
    )
    email = serializers.EmailField(
        source="user.email",
        read_only=True
    )
    first_name = serializers.CharField(
        source="user.first_name",
        read_only=True
    )
    last_name = serializers.CharField(
        source="user.last_name",
        read_only=True
    )

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "user",
            "username",
            "email",
            "first_name",
            "last_name",
            "gender",
            "course",
            "year_level",
            "age",
        ]
        read_only_fields = ["id", "user"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8
    )
    gender = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )
    course = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )
    year_level = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )
    age = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "gender",
            "course",
            "year_level",
            "age",
        ]

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "This username is already taken."
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        profile_data = {
            "gender": validated_data.pop("gender", None),
            "course": validated_data.pop("course", None),
            "year_level": validated_data.pop("year_level", None),
            "age": validated_data.pop("age", None),
        }

        password = validated_data.pop("password")

        user = User.objects.create_user(
            password=password,
            **validated_data
        )

        UserProfile.objects.create(
            user=user,
            **profile_data
        )

        return user





class PatientDoseSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()

    patient = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.select_related("user").all()
    )

    time = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    medicine_name = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True,
    )

    details = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True,
    )

    quantity = serializers.IntegerField(
        required=True,
        min_value=1,
    )

    class Meta:
        model = PatientDose
        fields = [
            "id",
            "patient",
            "patient_name",
            "medicine_name",
            "details",
            "time",
            "status",
            "quantity",
            "time_prescribe"
        ]
        read_only_fields = ["id", "patient_name", "time_prescribe"]

    def get_patient_name(self, obj):
        return (
            obj.patient.user.get_full_name()
            or obj.patient.user.username
        )



class RemindersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminders
        fields = [
            "id",
            "notification_type",
        ]
        read_only_fields = ["id"]

    def validate_notification_type(self, value):
        if value is not None:
            value = value.strip()

            if not value:
                raise serializers.ValidationError(
                    "Notification type cannot be empty."
                )

        return value



class PatientDoseHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientDoseHistory
        fields = [
            "id",
            "patient",
            "medicine_name",
            "status",
            "time_taken",
        ]
        read_only_fields = ["id", "time_taken"]

    def create(self, validated_data):
        from django.utils import timezone

        validated_data["time_taken"] = timezone.localtime().strftime(
            "%Y-%m-%d %I:%M:%S %p"
        )
        return super().create(validated_data)
