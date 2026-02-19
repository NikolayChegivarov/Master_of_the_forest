# forestry/urls
from django.urls import path

from Forest_apps.forestry.views.logging_site import logging_site_view
from Forest_apps.forestry.views.materials import materials_view
from Forest_apps.forestry.views.forestry import (
    forestry_view,
    create_forestry_view,
    edit_forestry_view,
    deactivate_forestry_view,
)


app_name = 'forestry'

urlpatterns = [
    path('', forestry_view, name='forestry'),  # Основная страница лесничеств

    path('logging-site/', logging_site_view, name='logging_site'),  # Лесосеки
    path('create/', create_forestry_view, name='create_forestry'),  # Создание лесосеки
    path('<int:forestry_id>/edit/', edit_forestry_view, name='edit_forestry'),  # Редактирование лесосеки
    path('<int:forestry_id>/deactivate/', deactivate_forestry_view, name='deactivate_forestry'),  # Деактивация лесосеки

    path('materials/', materials_view, name='materials'),  # Материалы
]
