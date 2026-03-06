from django.urls import path
from . import views

app_name = 'health'

urlpatterns = [
    path('', views.health, name='home'),
    path('chat/', views.health_chat, name='health_chat'),
    path('profile/save', views.health_profile, name='health_profile'),
    path('profile/get/', views.update_health_profile, name='update_health_profile'),
]