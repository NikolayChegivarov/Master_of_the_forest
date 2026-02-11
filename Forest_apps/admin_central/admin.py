# Forest_apps/admin_central/admin.py
from django.contrib import admin
from django.apps import apps


# 1. Core (Основные справочники)
@admin.register(apps.get_model('core', 'Position'))
class PositionAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']

@admin.register(apps.get_model('core', 'Warehouse'))
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']

@admin.register(apps.get_model('core', 'Vehicle'))
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['brand', 'model', 'license_plate', 'is_active']
    list_filter = ['is_active', 'brand']
    search_fields = ['brand', 'model', 'license_plate']

@admin.register(apps.get_model('core', 'Counterparty'))
class CounterpartyAdmin(admin.ModelAdmin):
    list_display = ['legal_form', 'name', 'inn', 'is_active']
    list_filter = ['legal_form', 'is_active']
    search_fields = ['name', 'inn', 'ogrn']

@admin.register(apps.get_model('core', 'Brigade'))
class BrigadeAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']

# 2. Employees (Сотрудники)
@admin.register(apps.get_model('employees', 'Employee'))
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'middle_name', 'position', 'warehouse', 'is_active']
    list_filter = ['position', 'warehouse', 'is_active']
    search_fields = ['last_name', 'first_name', 'middle_name']
    raw_id_fields = ['position', 'warehouse']

@admin.register(apps.get_model('employees', 'WorkTimeRecord'))
class WorkTimeRecordAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date_time', 'warehouse', 'hours']
    list_filter = ['warehouse', 'date_time']
    search_fields = ['employee__last_name', 'employee__first_name']
    date_hierarchy = 'date_time'

# 3. Forestry (Лесничества и материалы)
@admin.register(apps.get_model('forestry', 'Material'))
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['material_type', 'name']
    list_filter = ['material_type']
    search_fields = ['name']

@admin.register(apps.get_model('forestry', 'Forestry'))
class ForestryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']

@admin.register(apps.get_model('forestry', 'CuttingArea'))
class CuttingAreaAdmin(admin.ModelAdmin):
    list_display = ['forestry', 'quarter_number', 'division_number', 'area_hectares', 'is_active']
    list_filter = ['forestry', 'is_active']
    search_fields = ['quarter_number', 'division_number']
    raw_id_fields = ['forestry']

@admin.register(apps.get_model('forestry', 'CuttingAreaContent'))
class CuttingAreaContentAdmin(admin.ModelAdmin):
    list_display = ['cutting_area', 'material', 'quantity']
    list_filter = ['material__material_type']
    search_fields = ['cutting_area__quarter_number', 'material__name']
    raw_id_fields = ['cutting_area', 'material']

# 4. Inventory (Учет материалов)
@admin.register(apps.get_model('inventory', 'StorageLocation'))
class StorageLocationAdmin(admin.ModelAdmin):
    list_display = ['source_type', 'source_id', 'get_source_name']
    list_filter = ['source_type']
    search_fields = ['source_id']

    def get_source_name(self, obj):
        return obj.get_source_name()
    get_source_name.short_description = 'Название источника'

@admin.register(apps.get_model('inventory', 'MaterialMovement'))
class MaterialMovementAdmin(admin.ModelAdmin):
    list_display = ['accounting_type', 'date_time', 'material', 'quantity_display', 'is_completed']
    list_filter = ['accounting_type', 'is_completed', 'date_time']
    search_fields = ['material__name']
    date_hierarchy = 'date_time'
    readonly_fields = ['total_amount', 'completed_at']
    raw_id_fields = ['from_location', 'to_location', 'material', 'employee', 'vehicle']

@admin.register(apps.get_model('inventory', 'MaterialBalance'))
class MaterialBalanceAdmin(admin.ModelAdmin):
    list_display = ['storage_location', 'material', 'quantity_pieces', 'last_updated']
    list_filter = ['material__material_type']
    search_fields = ['material__name', 'storage_location__source_id']
    readonly_fields = ['last_updated']
    raw_id_fields = ['storage_location', 'material']

# 5. Operations (Учет операций)
@admin.register(apps.get_model('operations', 'OperationType'))
class OperationTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']

@admin.register(apps.get_model('operations', 'OperationRecord'))
class OperationRecordAdmin(admin.ModelAdmin):
    list_display = ['operation_type', 'date_time', 'warehouse', 'material', 'quantity']
    list_filter = ['operation_type', 'warehouse', 'date_time']
    search_fields = ['material__name']
    date_hierarchy = 'date_time'
    raw_id_fields = ['operation_type', 'warehouse', 'material']

# Настройка заголовков админки
admin.site.site_header = "Управление лесным хозяйством"
admin.site.site_title = "Лесное хозяйство"
admin.site.index_title = "Централизованная админ-панель"