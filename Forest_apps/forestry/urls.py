from django.urls import path
from Forest_apps.forestry.views.forestry import (
    forestry_view,
    create_forestry_view,
    edit_forestry_view,
    deactivate_forestry_view,
)
from Forest_apps.forestry.views.logging_site import (
    logging_site_view,
    create_logging_site_view,
    edit_logging_site_view,
    deactivate_logging_site_view,
    fill_logging_site_view,
    view_logging_site_view,
    remove_material_from_cutting_area_view,
    update_material_quantity_view,
)
from Forest_apps.forestry.views.materials import (
    materials_view,
    create_material_view,
    edit_material_view,
    deactivate_material_view,
    activate_material_view,
)

app_name = 'forestry'

urlpatterns = [
    # Лесничества
    path('', forestry_view, name='forestry'),
    path('create/', create_forestry_view, name='create_forestry'),
    path('<int:forestry_id>/edit/', edit_forestry_view, name='edit_forestry'),
    path('<int:forestry_id>/deactivate/', deactivate_forestry_view, name='deactivate_forestry'),

    # Лесосеки
    path('logging-site/', logging_site_view, name='logging_site'),
    path('logging-site/create/', create_logging_site_view, name='create_logging_site'),
    path('logging-site/<int:cutting_area_id>/edit/', edit_logging_site_view, name='edit_logging_site'),
    path('logging-site/<int:cutting_area_id>/deactivate/', deactivate_logging_site_view,
         name='deactivate_logging_site'),
    path('logging-site/<int:cutting_area_id>/fill/', fill_logging_site_view, name='fill_logging_site'),
    path('logging-site/<int:cutting_area_id>/view/', view_logging_site_view, name='view_logging_site'),
    path('logging-site/<int:cutting_area_id>/remove/<int:material_id>/', remove_material_from_cutting_area_view,
         name='remove_material'),
    path('logging-site/<int:cutting_area_id>/update/<int:material_id>/', update_material_quantity_view,
         name='update_material_quantity'),

    # Материалы
    path('materials/', materials_view, name='materials'),
    path('materials/create/', create_material_view, name='create_material'),
    path('materials/<int:material_id>/edit/', edit_material_view, name='edit_material'),
    path('materials/<int:material_id>/deactivate/', deactivate_material_view, name='deactivate_material'),
    path('materials/<int:material_id>/activate/', activate_material_view, name='activate_material'),
]