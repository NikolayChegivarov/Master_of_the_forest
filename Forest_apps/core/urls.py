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
from Forest_apps.core.views.Vehicle import (
    vehicle_list_view,
    vehicle_create_view,
    vehicle_edit_view,
    vehicle_deactivate_view,
)
from Forest_apps.core.views.Counterparty import (
    counterparty_list_view,
    counterparty_create_view,
    counterparty_edit_view,
    counterparty_deactivate_view,
)
from Forest_apps.core.views.Brigade import (
    brigade_list_view,
    brigade_create_view,
    brigade_edit_view,
    brigade_deactivate_view,
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

    # Транспорт
    path('vehicles/', vehicle_list_view, name='vehicle_list'),
    path('vehicles/create/', vehicle_create_view, name='vehicle_create'),
    path('vehicles/<int:vehicle_id>/edit/', vehicle_edit_view, name='vehicle_edit'),
    path('vehicles/<int:vehicle_id>/deactivate/', vehicle_deactivate_view, name='vehicle_deactivate'),

    # Контрагенты
    path('counterparties/', counterparty_list_view, name='counterparty_list'),
    path('counterparties/create/', counterparty_create_view, name='counterparty_create'),
    path('counterparties/<int:counterparty_id>/edit/', counterparty_edit_view, name='counterparty_edit'),
    path('counterparties/<int:counterparty_id>/deactivate/', counterparty_deactivate_view,
         name='counterparty_deactivate'),

    # Бригады
    path('brigades/', brigade_list_view, name='brigade_list'),
    path('brigades/create/', brigade_create_view, name='brigade_create'),
    path('brigades/<int:brigade_id>/edit/', brigade_edit_view, name='brigade_edit'),
    path('brigades/<int:brigade_id>/deactivate/', brigade_deactivate_view, name='brigade_deactivate'),
]