from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, EmailOrUsernameTokenObtainPairView, ProfileView, ChangePasswordView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', EmailOrUsernameTokenObtainPairView.as_view(), name='login'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', ProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
]
