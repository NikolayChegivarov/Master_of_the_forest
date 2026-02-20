# Forest_apps/core/urls.py
from django.urls import path
from Forest_apps.core.views.Warehouse import (
    warehouse_list_view,
    warehouse_create_view,
    warehouse_edit_view,
    warehouse_deactivate_view,
)
from Forest_apps.core.views.Position import (
    position_list_view,
    position_create_view,
    position_edit_view,
    position_deactivate_view,
)

app_name = 'core'

urlpatterns = [
    # Склады
    path('warehouses/', warehouse_list_view, name='warehouse_list'),
    path('warehouses/create/', warehouse_create_view, name='warehouse_create'),
    path('warehouses/<int:warehouse_id>/edit/', warehouse_edit_view, name='warehouse_edit'),
    path('warehouses/<int:warehouse_id>/deactivate/', warehouse_deactivate_view, name='warehouse_deactivate'),

    # Должности
    path('positions/', position_list_view, name='position_list'),
    path('positions/create/', position_create_view, name='position_create'),
    path('positions/<int:position_id>/edit/', position_edit_view, name='position_edit'),
    path('positions/<int:position_id>/deactivate/', position_deactivate_view, name='position_deactivate'),
]

