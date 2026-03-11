# Forest_apps/operations/urls.py
from django.urls import path
from Forest_apps.operations.views import operation_type, operation_record
from Forest_apps.operations.views import operations  # Добавить импорт для главной страницы

app_name = 'operations'

urlpatterns = [
    # Главная страница техпроцессов
    path('', operations.operations_home_view, name='operations_home'),

    # Типы операций
    path('types/', operation_type.operation_type_list_view, name='operation_type_list'),
    path('types/create/', operation_type.operation_type_create_view, name='operation_type_create'),
    path('types/<int:type_id>/edit/', operation_type.operation_type_edit_view, name='operation_type_edit'),
    path('types/<int:type_id>/toggle-active/', operation_type.operation_type_toggle_active_view,
         name='operation_type_toggle_active'),

    # Учет операций
    path('records/', operation_record.operation_record_list_view, name='operation_record_list'),
    path('records/create/', operation_record.operation_record_create_view, name='operation_record_create'),
    path('records/<int:record_id>/', operation_record.operation_record_detail_view, name='operation_record_detail'),
    path('records/<int:record_id>/edit/', operation_record.operation_record_edit_view, name='operation_record_edit'),
    path('records/<int:record_id>/delete/', operation_record.operation_record_delete_view,
         name='operation_record_delete'),

    # API для статистики
    path('api/stats/', operation_record.get_operation_stats, name='operation_stats'),
]