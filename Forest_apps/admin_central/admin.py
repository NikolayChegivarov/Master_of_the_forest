from django.contrib import admin
from django.contrib.auth.hashers import make_password
from django import forms
from django.contrib.auth.models import User
from django.apps import apps


# ========== 1. CORE (Основные справочники) ==========
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


# ========== 2. EMPLOYEES (Сотрудники) С КАСТОМНОЙ ФОРМОЙ ==========
class EmployeeAdminForm(forms.ModelForm):
    """Форма для создания/редактирования сотрудников с полем пароля"""

    password = forms.CharField(
        label='Пароль',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'vTextField'}),
        help_text='Оставьте пустым, чтобы не менять пароль. Нужен только для руководящих должностей.'
    )

    class Meta:
        model = apps.get_model('employees', 'Employee')
        fields = '__all__'

    # Убираем __init__, пусть Django сам подгружает

    def save(self, commit=True):
        instance = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            instance.password = make_password(password)
        if commit:
            instance.save()
            self.save_m2m()
        return instance


@admin.register(apps.get_model('employees', 'Employee'))
class EmployeeAdmin(admin.ModelAdmin):
    form = EmployeeAdminForm
    list_display = ['last_name', 'first_name', 'middle_name', 'position', 'warehouse', 'is_active', 'has_user']
    list_filter = ['position', 'warehouse', 'is_active']
    search_fields = ['last_name', 'first_name', 'middle_name']

    # Убираем raw_id_fields для position, оставляем только для warehouse если нужно
    raw_id_fields = []  # Временно пусто

    fieldsets = (
        ('Личная информация', {
            'fields': ('last_name', 'first_name', 'middle_name')
        }),
        ('Рабочая информация', {
            'fields': ('position', 'warehouse', 'is_active')
        }),
        ('Аутентификация', {
            'fields': ('password',),
            'classes': ('wide',),
        }),
    )

    def has_user(self, obj):
        try:
            User.objects.get(username=f"employee_{obj.id}")
            return True
        except User.DoesNotExist:
            return False

    has_user.short_description = 'Есть доступ'
    has_user.boolean = True

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        руководящие_должности = [
            'Руководитель', 'Бухгалтер', 'Механик',
            'Мастер ЛПЦ', 'Мастер ДОЦ', 'Мастер ЖД'
        ]

        if obj.position and obj.position.name in руководящие_должности:
            username = f"employee_{obj.id}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': obj.first_name,
                    'last_name': obj.last_name,
                }
            )
            password = form.cleaned_data.get('password')
            if password:
                user.set_password(password)
            user.is_staff = True
            user.save()

# ========== 2.1. WORK TIME RECORDS (Учет рабочего времени) ==========
@admin.register(apps.get_model('employees', 'WorkTimeRecord'))
class WorkTimeRecordAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date_time', 'warehouse', 'hours']
    list_filter = ['warehouse', 'date_time']
    search_fields = ['employee__last_name', 'employee__first_name']
    date_hierarchy = 'date_time'
    raw_id_fields = ['employee', 'warehouse']

# ========== 3. FORESTRY (Лесничества и материалы) ==========
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


# ========== 4. INVENTORY (Учет материалов) ==========
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

    def quantity_display(self, obj):
        return f"{obj.quantity_pieces} шт"

    quantity_display.short_description = 'Количество'


@admin.register(apps.get_model('inventory', 'MaterialBalance'))
class MaterialBalanceAdmin(admin.ModelAdmin):
    list_display = ['storage_location', 'material', 'quantity_pieces', 'last_updated']
    list_filter = ['material__material_type']
    search_fields = ['material__name', 'storage_location__source_id']
    readonly_fields = ['last_updated']
    raw_id_fields = ['storage_location', 'material']


# ========== 5. OPERATIONS (Учет операций) ==========
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