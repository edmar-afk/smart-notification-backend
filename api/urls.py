from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

# ssd
urlpatterns = [
    # path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),

    path("scan-school-id/", views.scan_school_id, name="scan_school_id"),
]