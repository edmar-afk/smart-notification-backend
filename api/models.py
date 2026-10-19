from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator



class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.TextField(blank=True, null=True)
    course = models.TextField(blank=True, null=True)
    year_level = models.TextField(blank=True, null=True)
    age = models.TextField(blank=True, null=True)
    def __str__(self):
        return self.user.username
    


class Appointment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    status = models.TextField(default='Pending')
    description = models.TextField(blank=True, null=True)
    symptoms = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Appointment for {self.user.username} on {self.date} at {self.time}"


class Patients(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    condition = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.user.first_name
    

from django.db import models
from django.contrib.auth.models import User


class DoseSchedule(models.Model):
    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Completed", "Completed"),
        ("Paused", "Paused"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="dose_schedules",
    )

    medication_name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100, blank=True, default="")

    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)

    # Time of day the medication should be taken.
    scheduled_time = models.TimeField()

    # Total planned administrations for this schedule, if known.
    total_doses = models.PositiveIntegerField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Active",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.medication_name} for {self.user.username}"


class DoseRecord(models.Model):
    STATUS_CHOICES = [
        ("Upcoming", "Upcoming"),
        ("Taken", "Taken"),
        ("Missed", "Missed"),
    ]

    dose_schedule = models.ForeignKey(
        DoseSchedule,
        on_delete=models.CASCADE,
        related_name="dose_records",
    )

    scheduled_at = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Upcoming",
    )

    taken_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["scheduled_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["dose_schedule", "scheduled_at"],
                name="unique_scheduled_dose",
            )
        ]

    def __str__(self):
        return (
            f"{self.dose_schedule.medication_name} - "
            f"{self.scheduled_at} ({self.status})"
        )
