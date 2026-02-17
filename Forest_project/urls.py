# Forest_project/urls.py
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),  # админка
    path('admin_central/', include('Forest_apps.admin_central.urls')),  # дашборд админки

    path('', lambda request: redirect('authorization:login'), name='root'),  # редирект на страницу авторизации
    path('authorization/', include('Forest_apps.authorization.urls')),  # авторизация
    path('employees/', include('Forest_apps.employees.urls')),  # сотрудники
    path('forestry/', include('Forest_apps.forestry.urls')),  # лесничества, лесосеки, материалы
]