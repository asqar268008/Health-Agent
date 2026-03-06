# myapp/urls.py
from django.urls import path 
from . import views

app_name = 'myapp'

urlpatterns = [
    path('', views.home, name='home'),
    path('csrf/', views.get_csrf_token, name='get_csrf_token'),
    path('login/', views.api_login, name='api_login'),
    path('signup/', views.api_signup, name='api_signup'),
    path('logout/', views.logout_view, name='logout_view'),
    path('auth-status/', views.check_auth_status, name='auth_status'),
]