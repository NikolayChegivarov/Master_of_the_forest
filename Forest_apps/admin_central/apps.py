# admin_central/apps.py
from django.apps import AppConfig

class AdminCentralConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin_central'
    verbose_name = 'Централизованная админка'
