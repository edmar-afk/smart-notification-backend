
from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('login/',views.CustomTokenObtainPairView.as_view(),name='token_obtain_pair'),
    path('register/',views.RegisterView.as_view(),name='register'),
    path('profile/',views.UserProfileView.as_view(),name='user-profile'),
    path('token/refresh/',TokenRefreshView.as_view(),name='token_refresh'),
    
    path("patients/",views.PatientListView.as_view(),name="patient-list",),
    
    path("patients/",views.PatientListView.as_view(),name="patient-list",),
    path("patient-doses/",views.PatientDoseListCreateView.as_view(),name="patient-dose-list-create",),
    path("patient-doses/<int:pk>/",views.PatientDoseDetailView.as_view(),name="patient-dose-detail",),
]
