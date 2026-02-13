# admin_central/urls.py
from django.urls import path
from . import views

app_name = 'admin_central'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='admin_dashboard'),
]