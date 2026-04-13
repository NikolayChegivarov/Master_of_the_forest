from django.urls import path
from Forest_apps.forestry.views.forestry import (
    forestry_view,
    create_forestry_view,
    edit_forestry_view,
    deactivate_forestry_view, activate_forestry_view
)
from Forest_apps.forestry.views.logging_site import (
    logging_site_view,
    create_cutting_area_view,
    edit_cutting_area_view,
    deactivate_cutting_area_view,
    fill_cutting_area_view,
    view_cutting_area_view,
    update_material_quantity_view,
    remove_material_view, activate_cutting_area_view
)
from Forest_apps.forestry.views.materials import (
    materials_view,
    material_create_view,
    material_edit_view,
    material_delete_view
)

app_name = 'forestry'

urlpatterns = [
    # Лесничества
    path('', forestry_view, name='forestry'),
    path('create/', create_forestry_view, name='create_forestry'),
    path('<int:forestry_id>/edit/', edit_forestry_view, name='edit_forestry'),
    path('<int:forestry_id>/deactivate/', deactivate_forestry_view, name='deactivate_forestry'),
    path('<int:forestry_id>/activate/', activate_forestry_view, name='activate_forestry'),

    # Лесосеки - ИСПОЛЬЗУЕМ ИМЕНА ИЗ ВАШИХ ШАБЛОНОВ
    path('logging-site/', logging_site_view, name='logging_site'),
    path('logging-site/create/', create_cutting_area_view, name='create_logging_site'),
    path('logging-site/<int:area_id>/edit/', edit_cutting_area_view, name='edit_logging_site'),
    path('logging-site/<int:area_id>/deactivate/', deactivate_cutting_area_view, name='deactivate_logging_site'),
    path('logging-site/<int:area_id>/activate/', activate_cutting_area_view, name='activate_logging_site'),
    # 👈 deactivate_logging_site
    path('logging-site/<int:area_id>/fill/', fill_cutting_area_view, name='fill_logging_site'),
    path('logging-site/<int:area_id>/view/', view_cutting_area_view, name='view_logging_site'),
    path('logging-site/<int:area_id>/update-material/<int:material_id>/', update_material_quantity_view,
         name='update_material_quantity'),
    path('logging-site/<int:area_id>/remove-material/<int:material_id>/', remove_material_view, name='remove_material'),

    # Материалы
    path('materials/', materials_view, name='materials'),
    path('materials/create/', material_create_view, name='material_create'),
    path('materials/<int:material_id>/edit/', material_edit_view, name='material_edit'),
    path('materials/<int:material_id>/delete/', material_delete_view, name='material_delete'),
]