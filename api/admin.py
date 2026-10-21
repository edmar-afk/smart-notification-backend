from django.contrib import admin
from .models import PatientDose, PatientDoseHistory

admin.site.register(PatientDose)
admin.site.register(PatientDoseHistory)