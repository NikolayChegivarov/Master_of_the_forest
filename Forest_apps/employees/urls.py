from django.urls import path
from Forest_apps.employees.views.employee import (
    employee_list_view,
    employee_detail_view,
    employee_create_view,
    employee_edit_view,
    employee_deactivate_view,
    employee_activate_view,
)
from Forest_apps.employees.views.workTimeRecord import (
    worktime_list_view,
    worktime_create_view,
    worktime_edit_view,
    worktime_delete_view,
    worktime_employee_report_view,
    worktime_warehouse_report_view,
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

    # Учет рабочего времени
    path('worktime/', worktime_list_view, name='worktime_list'),
    path('worktime/create/', worktime_create_view, name='worktime_create'),
    path('worktime/<int:record_id>/edit/', worktime_edit_view, name='worktime_edit'),
    path('worktime/<int:record_id>/delete/', worktime_delete_view, name='worktime_delete'),
    path('worktime/employee/<int:employee_id>/', worktime_employee_report_view, name='worktime_employee_report'),
    path('worktime/warehouse/<int:warehouse_id>/', worktime_warehouse_report_view, name='worktime_warehouse_report'),
]