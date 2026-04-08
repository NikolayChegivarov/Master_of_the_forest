from django.urls import path
from Forest_apps.inventory.views import storage_location
from Forest_apps.inventory.views import material_balance
from Forest_apps.inventory.views import material_movement
from Forest_apps.inventory.views import conversion

app_name = 'inventory'

urlpatterns = [
    # Места хранения
    # Места хранения
    path('storage-locations/', storage_location.storage_location_list_view, name='storage_location_list'),
    path('storage-locations/my/', storage_location.my_storage_location_list_view, name='my_storage_location_list'),
    path('storage-locations/<int:location_id>/', storage_location.storage_location_detail_view, name='storage_location_detail'),
    path('storage-locations/my/<int:location_id>/', storage_location.my_storage_location_detail_view, name='my_storage_location_detail'),

    # Остатки материалов
    path('balances/', material_balance.material_balance_list_view, name='material_balance_list'),
    path('balances/create/', material_balance.material_balance_create_view, name='material_balance_create'),
    path('balances/<int:balance_id>/', material_balance.material_balance_detail_view, name='material_balance_detail'),

    # Поступления материалов
    path('receipts/', material_balance.receipt_list_view, name='receipt_list'),
    path('receipts/<int:receipt_id>/', material_balance.receipt_detail_view, name='receipt_detail'),
    path('receipts/<int:receipt_id>/edit/', material_balance.receipt_edit_view, name='receipt_edit'),
    path('receipts/<int:receipt_id>/delete/', material_balance.receipt_delete_view, name='receipt_delete'),

    # Движения материалов
    path('movements/', material_movement.material_movement_list_view, name='material_movement_list'),
    path('movements/create/', material_movement.material_movement_create_view, name='material_movement_create'),
    path('movements/<int:movement_id>/', material_movement.material_movement_detail_view,
         name='material_movement_detail'),
    path('movements/<int:movement_id>/edit/', material_movement.material_movement_edit_view,
         name='material_movement_edit'),
    path('movements/<int:movement_id>/delete/', material_movement.material_movement_delete_view,
         name='material_movement_delete'),
    path('movements/<int:movement_id>/execute/', material_movement.material_movement_execute_view,
         name='material_movement_execute'),
    path('movements/<int:movement_id>/cancel/', material_movement.material_movement_cancel_view,
         name='material_movement_cancel'),
    path('movements/<int:movement_id>/confirm/', material_movement.material_movement_confirm_shipment_view,
         name='material_movement_confirm'),
    path('movements/pending-shipments/', material_movement.material_movement_pending_shipments_view,
         name='material_movement_pending_shipments'),

    # API
    path('api/locations-by-type/', material_movement.get_locations_by_type, name='api_locations_by_type'),
    path('api/materials/', material_movement.get_materials, name='api_materials'),

    # Конвертация древесины
    path('conversions/', conversion.conversion_list_view, name='conversion_list'),
    path('conversions/create/', conversion.conversion_create_view, name='conversion_create'),
    path('conversions/<int:conversion_id>/', conversion.conversion_detail_view, name='conversion_detail'),
]