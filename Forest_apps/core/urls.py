# Forest_apps/core/urls.py
from django.urls import path
from Forest_apps.core.views.Warehouse import (
    warehouse_list_view,
    warehouse_create_view,
    warehouse_edit_view,
    warehouse_deactivate_view,
)

app_name = 'core'

urlpatterns = [
    # Склады
    path('warehouses/', warehouse_list_view, name='warehouse_list'),
    path('warehouses/create/', warehouse_create_view, name='warehouse_create'),
    path('warehouses/<int:warehouse_id>/edit/', warehouse_edit_view, name='warehouse_edit'),
    path('warehouses/<int:warehouse_id>/deactivate/', warehouse_deactivate_view, name='warehouse_deactivate'),

    # Здесь позже будут другие URL для должностей, транспорта, контрагентов, бригад
]


