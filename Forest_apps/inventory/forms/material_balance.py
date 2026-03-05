from django import forms
from django.core.exceptions import ValidationError
from Forest_apps.inventory.models import MaterialBalance, StorageLocation
from Forest_apps.forestry.models import Material
from Forest_apps.core.models import Warehouse, Brigade, Vehicle


class MaterialBalanceFilterForm(forms.Form):
    """Форма фильтрации остатков материалов"""
    storage_location = forms.ModelChoiceField(
        queryset=StorageLocation.objects.all().order_by('source_type'),
        required=False,
        label='Место хранения',
        widget=forms.Select(attrs={'class': 'form-control auto-submit'})
    )

    material_type = forms.ChoiceField(
        choices=[('', 'Все типы')] + Material.MATERIAL_TYPE_CHOICES,
        required=False,
        label='Тип материала',
        widget=forms.Select(attrs={'class': 'form-control auto-submit'})
    )

    material = forms.ModelChoiceField(
        queryset=Material.objects.all().order_by('name'),
        required=False,
        label='Материал',
        widget=forms.Select(attrs={'class': 'form-control auto-submit'})
    )

    search = forms.CharField(
        required=False,
        label='Поиск',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по названию...'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Если выбран тип материала, фильтруем материалы по типу
        if self.data.get('material_type'):
            self.fields['material'].queryset = Material.objects.filter(
                material_type=self.data.get('material_type')
            ).order_by('name')


class MaterialBalanceCreateForm(forms.ModelForm):
    """Форма создания остатка материала"""

    class Meta:
        model = MaterialBalance
        fields = ['storage_location', 'material', 'quantity_pieces', 'quantity_meters', 'quantity_cubic']
        widgets = {
            'storage_location': forms.Select(attrs={
                'class': 'form-control',
                'autofocus': True
            }),
            'material': forms.Select(attrs={
                'class': 'form-control'
            }),
            'quantity_pieces': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Количество в штуках',
                'step': '0.001',
                'min': '0'
            }),
            'quantity_meters': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Количество в погонных метрах',
                'step': '0.001',
                'min': '0'
            }),
            'quantity_cubic': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Количество в кубических метрах',
                'step': '0.001',
                'min': '0'
            }),
        }
        labels = {
            'storage_location': 'Место хранения',
            'material': 'Материал',
            'quantity_pieces': 'Штуки',
            'quantity_meters': 'Погонные метры',
            'quantity_cubic': 'Кубические метры',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

        # Получаем все места хранения
        all_locations = StorageLocation.objects.all().order_by('source_type')

        # Фильтруем только те места, которые принадлежат пользователю
        user_locations = []
        for location in all_locations:
            if self.is_owned_by_user(location):
                user_locations.append(location.id)

        # Устанавливаем queryset только для своих мест хранения
        self.fields['storage_location'].queryset = StorageLocation.objects.filter(
            id__in=user_locations
        ).order_by('source_type')

        self.fields['material'].queryset = Material.objects.all().order_by('material_type', 'name')

    def is_owned_by_user(self, location):
        """Проверяет, принадлежит ли место хранения пользователю"""
        if not self.user or not self.user.is_authenticated:
            return False

        from Forest_apps.core.models import Warehouse, Brigade, Vehicle

        try:
            if location.source_type == 'склад':
                return Warehouse.objects.filter(id=location.source_id, created_by=self.user).exists()
            elif location.source_type == 'бригады':
                return Brigade.objects.filter(id=location.source_id, created_by=self.user).exists()
            elif location.source_type == 'автомобиль':
                return Vehicle.objects.filter(id=location.source_id, created_by=self.user).exists()
            elif location.source_type == 'контрагент':
                # Контрагенты всегда чужие, нельзя создавать на них остатки
                return False
        except:
            pass

        return False

    def clean(self):
        """Валидация - хотя бы одно количество должно быть указано"""
        cleaned_data = super().clean()
        quantity_pieces = cleaned_data.get('quantity_pieces')
        quantity_meters = cleaned_data.get('quantity_meters')
        quantity_cubic = cleaned_data.get('quantity_cubic')

        if not quantity_pieces and not quantity_meters and not quantity_cubic:
            raise forms.ValidationError('Необходимо указать хотя бы одно количество')

        return cleaned_data

    def validate_unique(self):
        """
        Переопределяем метод validate_unique, чтобы отключить стандартную
        проверку уникальности для пары (storage_location, material)
        """
        try:
            self.instance.validate_unique()
        except ValidationError as e:
            # Игнорируем ошибку уникальности для нашей пары полей
            if 'unique_material_balance' in e.error_dict:
                # Удаляем эту ошибку из списка
                pass
            else:
                # Если есть другие ошибки - пробрасываем их
                raise e

    def save(self, commit=True):
        """
        Переопределяем метод save, чтобы вместо создания нового остатка
        обновлять существующий, если он уже есть
        """
        storage_location = self.cleaned_data['storage_location']
        material = self.cleaned_data['material']

        # Пытаемся найти существующий остаток
        try:
            existing_balance = MaterialBalance.objects.get(
                storage_location=storage_location,
                material=material
            )

            # Если нашли существующий, обновляем его поля
            existing_balance.quantity_pieces += self.cleaned_data.get('quantity_pieces', 0) or 0
            existing_balance.quantity_meters = (existing_balance.quantity_meters or 0) + (
                        self.cleaned_data.get('quantity_meters', 0) or 0)
            existing_balance.quantity_cubic = (existing_balance.quantity_cubic or 0) + (
                        self.cleaned_data.get('quantity_cubic', 0) or 0)

            if commit:
                existing_balance.save()

            return existing_balance

        except MaterialBalance.DoesNotExist:
            # Если не нашли, создаем новый
            return super().save(commit=commit)