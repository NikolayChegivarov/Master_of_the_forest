from django.urls import path
from . import views

app_name = 'employees'  # 👈 Это регистрирует namespace

urlpatterns = [
    # Список сотрудников
    # path('', views.employees_list, name='employees_list'),

    # Добавьте другие URL-ы по необходимости
    # path('<int:pk>/', views.employee_detail, name='employee_detail'),
    # path('add/', views.employee_add, name='employee_add'),
    # path('<int:pk>/edit/', views.employee_edit, name='employee_edit'),
    # path('<int:pk>/delete/', views.employee_delete, name='employee_delete'),
]