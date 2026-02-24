from django.urls import path
from Forest_apps.inventory.views import storage_location
from Forest_apps.inventory.views import material_balance

app_name = 'inventory'

urlpatterns = [
    # Места хранения
    path('storage-locations/', storage_location.storage_location_list_view, name='storage_location_list'),
    path('storage-locations/<int:location_id>/', storage_location.storage_location_detail_view,
         name='storage_location_detail'),

    # Остатки материалов
    path('balances/', material_balance.material_balance_list_view, name='material_balance_list'),
    path('balances/create/', material_balance.material_balance_create_view, name='material_balance_create'),
    path('balances/<int:balance_id>/edit/', material_balance.material_balance_edit_view, name='material_balance_edit'),
    path('balances/<int:balance_id>/delete/', material_balance.material_balance_delete_view,
         name='material_balance_delete'),
    path('balances/<int:balance_id>/', material_balance.material_balance_detail_view, name='material_balance_detail'),
]