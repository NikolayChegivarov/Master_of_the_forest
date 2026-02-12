# Forest_project/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin_central/', include('admin_central.urls')),
    path('', include('Forest_apps.core.urls')),  # ✅ Подключаем urls core
]
