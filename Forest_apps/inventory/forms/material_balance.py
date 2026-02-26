from django import forms
from Forest_apps.inventory.models import MaterialBalance, StorageLocation
from Forest_apps.forestry.models import Material


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


class MaterialBalanceFilterForm(forms.Form):
    """Форма для фильтрации остатков"""

    storage_location = forms.ModelChoiceField(
        label='Место хранения',
        required=False,
        queryset=StorageLocation.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    material_type = forms.ChoiceField(
        label='Тип материала',
        required=False,
        choices=[('', 'Все типы')] + Material.MATERIAL_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    material = forms.ModelChoiceField(
        label='Материал',
        required=False,
        queryset=Material.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    search = forms.CharField(
        label='Поиск',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по материалу или месту...'
        })
    )