
from django.urls import path
from . import views

from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    # Authentication
    path(
        "login/",
        views.CustomTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),

    path(
        "register/",
        views.RegisterView.as_view(),
        name="register",
    ),

    path(
        "profile/",
        views.UserProfileView.as_view(),
        name="user-profile",
    ),

    path(
        "token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),

    # Patients
    path(
        "patients/",
        views.PatientListView.as_view(),
        name="patient-list",
    ),

    # Permanent user deletion
    path(
        "users/<int:pk>/",
        views.PermanentUserDeleteView.as_view(),
        name="permanent-user-delete",
    ),

    # Patient doses
    path(
        "patient-doses/",
        views.PatientDoseListCreateView.as_view(),
        name="patient-dose-list-create",
    ),

    path(
        "patient-doses/<int:pk>/",
        views.PatientDoseDetailView.as_view(),
        name="patient-dose-detail",
    ),

    path(
        "patient-doses/user/<int:user_id>/",
        views.PatientDoseListView.as_view(),
        name="patient-dose-list",
    ),

    path(
        "patient-doses/<int:pk>/restore/",
        views.RestorePatientDoseView.as_view(),
        name="patient-dose-restore",
    ),

    # Reminders
    path(
        "reminders/",
        views.StudentReminderView.as_view(),
        name="student-reminders",
    ),

    # Global dose history (admin dashboard)
    # Keep this before the user-specific history routes.
    path(
        "patient-dose-history/",
        views.AllPatientDoseHistoryListView.as_view(),
        name="all-patient-dose-history",
    ),

    # Dose history by user
    path(
        "patient-dose-history/<int:user_id>/",
        views.PatientDoseHistoryListCreateView.as_view(),
        name="patient-dose-history-list-create",
    ),

    # Individual dose history
    path(
        "patient-dose-history/<int:user_id>/<int:pk>/",
        views.PatientDoseHistoryDetailView.as_view(),
        name="patient-dose-history-detail",
    ),

    # Restore dose history
    path(
        "patient-dose-history/<int:user_id>/<int:pk>/restore/",
        views.RestorePatientDoseHistoryView.as_view(),
        name="patient-dose-history-restore",
    ),
    
    
    
    path(
    "patient-doses/<int:pk>/permanent-delete/",
    views.PermanentDeletePatientDoseView.as_view(),
    name="permanent-delete-patient-dose"
),

path(
    "patient-dose-history/<int:user_id>/<int:pk>/permanent-delete/",
    views.PermanentDeletePatientDoseHistoryView.as_view(),
    name="permanent-delete-patient-dose-history"
),
]
