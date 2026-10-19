
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers

from .models import UserProfile, DoseSchedule, DoseRecord


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




class DoseRecordSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(
        source="dose_schedule.medication_name",
        read_only=True,
    )
    dosage = serializers.CharField(
        source="dose_schedule.dosage",
        read_only=True,
    )
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = DoseRecord
        fields = [
            "id",
            "dose_schedule",
            "patient_name",
            "medication_name",
            "dosage",
            "scheduled_at",
            "status",
            "taken_at",
            "notes",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "patient_name",
            "medication_name",
            "dosage",
            "created_at",
        ]

    def get_patient_name(self, obj):
        user = obj.dose_schedule.user
        return user.get_full_name() or user.username


class DoseScheduleSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    dose_records = DoseRecordSerializer(many=True, read_only=True)

    doses_taken = serializers.SerializerMethodField()
    upcoming_doses = serializers.SerializerMethodField()
    missed_doses = serializers.SerializerMethodField()

    class Meta:
        model = DoseSchedule
        fields = [
            "id",
            "user",
            "patient_name",
            "medication_name",
            "dosage",
            "frequency",
            "start_date",
            "end_date",
            "scheduled_time",
            "total_doses",
            "status",
            "created_at",
            "dose_records",
            "doses_taken",
            "upcoming_doses",
            "missed_doses",
        ]
        read_only_fields = [
            "id",
            "patient_name",
            "created_at",
            "dose_records",
            "doses_taken",
            "upcoming_doses",
            "missed_doses",
        ]

    def get_patient_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_doses_taken(self, obj):
        return obj.dose_records.filter(status="Taken").count()

    def get_upcoming_doses(self, obj):
        return obj.dose_records.filter(status="Upcoming").count()

    def get_missed_doses(self, obj):
        return obj.dose_records.filter(status="Missed").count()