from django.urls import path
from . import views


app_name = 'admin_central'

urlpatterns = [
    # === ДАШБОРД С АНАЛИТИКОЙ ===
    path('dashboard/', views.dashboard_view, name='dashboard'),
]