# myapp/urls.py

from django.urls import path
from . import views

app_name = "myapp"

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.api_login, name='login'),
    path('signup/', views.api_signup, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('auth-status/', views.check_auth_status, name='auth_status'),
    path('health/', views.health, name='health'),
    path('health/chat/', views.health_chat, name='health_chat'),
    path('health/profile/save/', views.save_health_profile, name='save_health_profile'),
    path('health/profile/get/', views.get_health_profile, name='get_health_profile'),
]