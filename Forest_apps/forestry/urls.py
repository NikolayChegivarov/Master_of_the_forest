# forestry/urls
from django.urls import path
from Forest_apps.forestry.views.forestry import forestry_view
from Forest_apps.forestry.views.logging_site import logging_site_view
from Forest_apps.forestry.views.materials import materials_view


app_name = 'forestry'

urlpatterns = [
    path('', forestry_view, name='forestry'),  # Основная страница лесничеств
    path('logging-site/', logging_site_view, name='logging_site'),  # Лесосека
    path('materials/', materials_view, name='materials'),  # Материалы
]
