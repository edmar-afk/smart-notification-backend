
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers

from .models import UserProfile, PatientDose, Patients


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
        queryset=Patients.objects.select_related("user").all()
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
        ]
        read_only_fields = ["id", "patient_name"]

    def get_patient_name(self, obj):
        return obj.patient.user.get_full_name() or obj.patient.user.username
