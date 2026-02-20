from django.urls import path
from Forest_apps.employees.views.employee import (
    employee_list_view,
    employee_detail_view,
    employee_create_view,
    employee_edit_view,
    employee_deactivate_view,
    employee_activate_view,
)

app_name = 'employees'

urlpatterns = [
    # Сотрудники
    path('', employee_list_view, name='employee_list'),
    path('create/', employee_create_view, name='employee_create'),
    path('<int:employee_id>/', employee_detail_view, name='employee_detail'),
    path('<int:employee_id>/edit/', employee_edit_view, name='employee_edit'),
    path('<int:employee_id>/deactivate/', employee_deactivate_view, name='employee_deactivate'),
    path('<int:employee_id>/activate/', employee_activate_view, name='employee_activate'),
]