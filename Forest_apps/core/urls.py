# Forest_apps/core/urls.py
from django.urls import path
from .views import management

app_name = 'core'


urlpatterns = [
    # Маршруты для руководящего состава
    path('supervisor/', management.supervisor_dashboard, name='supervisor_dashboard'),
    path('employees/', management.employees_list, name='employees_list'),
    path('counterparties/', management.counterparties_list, name='counterparties_list'),
    path('external/', management.external_interfaces, name='external_interfaces'),
]