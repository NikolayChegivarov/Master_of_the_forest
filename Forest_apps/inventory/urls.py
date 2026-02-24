from django.urls import path

from Forest_apps.inventory.views.storage_location import (
    storage_location_list_view,
    storage_location_detail_view,
)

app_name = 'inventory'

urlpatterns = [
    # Места хранения
    path('storage-locations/', storage_location_list_view, name='storage_location_list'),
    path('storage-locations/<int:location_id>/', storage_location_detail_view, name='storage_location_detail'),

    # Здесь позже будут другие URL для движения материалов и остатков
]