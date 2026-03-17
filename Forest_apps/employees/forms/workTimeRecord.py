from django import forms
from django.utils import timezone
from Forest_apps.employees.models import WorkTimeRecord, Employee
from Forest_apps.core.models import Warehouse, Position


class WorkTimeRecordCreateForm(forms.ModelForm):
    """Форма создания записи рабочего времени"""

    class Meta:
        model = WorkTimeRecord
        fields = ['date_time', 'warehouse', 'employee', 'hours']
        widgets = {
            'date_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
                'autofocus': True
            }),
            'warehouse': forms.Select(attrs={
                'class': 'form-control'
            }),
            'employee': forms.Select(attrs={
                'class': 'form-control'
            }),
            'hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите количество часов',
                'step': '0.25',
                'min': '0'
            }),
        }
        labels = {
            'date_time': 'Дата и время',
            'warehouse': 'Склад',
            'employee': 'Сотрудник',
            'hours': 'Часы работы',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.user_position = kwargs.pop('user_position', None)
        super().__init__(*args, **kwargs)

        # Получаем ID складов, принадлежащих должности пользователя
        user_warehouse_ids = self._get_user_warehouse_ids()

        # Ограничиваем выбор складов только теми, что принадлежат должности пользователя
        self.fields['warehouse'].queryset = Warehouse.objects.filter(
            id__in=user_warehouse_ids,
            is_active=True
        ).order_by('name')

        # Ограничиваем выбор сотрудников только теми, кто привязан к этим складам
        self.fields['employee'].queryset = Employee.objects.filter(
            warehouse_id__in=user_warehouse_ids,
            is_active=True
        ).select_related('position').order_by('last_name', 'first_name')

        # Устанавливаем начальное значение даты на сегодня
        self.fields['date_time'].initial = timezone.now().strftime('%Y-%m-%dT%H:%M')

    def _get_user_warehouse_ids(self):
        """Получает ID складов, принадлежащих должности пользователя"""
        if not self.user_position:
            return []

        try:
            # Находим должность по названию
            position = Position.objects.get(name__iexact=self.user_position)

            # Находим все склады, созданные этой должностью
            warehouses = Warehouse.objects.filter(
                created_by_position=position,
                is_active=True
            ).values_list('id', flat=True)

            return list(warehouses)
        except Position.DoesNotExist:
            return []

    def clean_hours(self):
        """Валидация количества часов"""
        hours = self.cleaned_data['hours']
        if hours <= 0:
            raise forms.ValidationError('Количество часов должно быть больше 0')
        if hours > 24:
            raise forms.ValidationError('Количество часов не может превышать 24')
        return hours

    def clean(self):
        """Дополнительная валидация"""
        cleaned_data = super().clean()
        date_time = cleaned_data.get('date_time')
        employee = cleaned_data.get('employee')
        warehouse = cleaned_data.get('warehouse')

        # Проверка на будущие даты
        if date_time and date_time > timezone.now():
            raise forms.ValidationError('Нельзя создавать записи на будущее время')

        # Проверка, что сотрудник действительно привязан к выбранному складу
        if employee and warehouse and employee.warehouse_id != warehouse.id:
            raise forms.ValidationError(
                f'Сотрудник {employee.short_name} не привязан к складу "{warehouse.name}"'
            )

        # Проверка на дубликаты записей для сотрудника в один день
        if date_time and employee:
            existing_record = WorkTimeRecord.objects.filter(
                employee=employee,
                date_time__date=date_time.date()
            ).exists()

            if existing_record:
                raise forms.ValidationError(
                    f'Для сотрудника {employee.short_name} уже есть запись на {date_time.date()}'
                )

        return cleaned_data


class WorkTimeRecordEditForm(forms.ModelForm):
    """Форма редактирования записи рабочего времени"""

    class Meta:
        model = WorkTimeRecord
        fields = ['date_time', 'warehouse', 'employee', 'hours']
        widgets = {
            'date_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'warehouse': forms.Select(attrs={
                'class': 'form-control'
            }),
            'employee': forms.Select(attrs={
                'class': 'form-control'
            }),
            'hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите количество часов',
                'step': '0.25',
                'min': '0'
            }),
        }
        labels = {
            'date_time': 'Дата и время',
            'warehouse': 'Склад',
            'employee': 'Сотрудник',
            'hours': 'Часы работы',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.user_position = kwargs.pop('user_position', None)
        super().__init__(*args, **kwargs)

        # Получаем ID складов, принадлежащих должности пользователя
        user_warehouse_ids = self._get_user_warehouse_ids()

        # Ограничиваем выбор складов только теми, что принадлежат должности пользователя
        self.fields['warehouse'].queryset = Warehouse.objects.filter(
            id__in=user_warehouse_ids,
            is_active=True
        ).order_by('name')

        # Ограничиваем выбор сотрудников только теми, кто привязан к этим складам
        self.fields['employee'].queryset = Employee.objects.filter(
            warehouse_id__in=user_warehouse_ids,
            is_active=True
        ).select_related('position').order_by('last_name', 'first_name')

        # Форматируем дату для поля ввода
        if self.instance and self.instance.date_time:
            self.fields['date_time'].initial = self.instance.date_time.strftime('%Y-%m-%dT%H:%M')

    def _get_user_warehouse_ids(self):
        """Получает ID складов, принадлежащих должности пользователя"""
        if not self.user_position:
            return []

        try:
            # Находим должность по названию
            position = Position.objects.get(name__iexact=self.user_position)

            # Находим все склады, созданные этой должностью
            warehouses = Warehouse.objects.filter(
                created_by_position=position,
                is_active=True
            ).values_list('id', flat=True)

            return list(warehouses)
        except Position.DoesNotExist:
            return []

    def clean_hours(self):
        """Валидация количества часов"""
        hours = self.cleaned_data['hours']
        if hours <= 0:
            raise forms.ValidationError('Количество часов должно быть больше 0')
        if hours > 24:
            raise forms.ValidationError('Количество часов не может превышать 24')
        return hours

    def clean(self):
        """Дополнительная валидация"""
        cleaned_data = super().clean()
        date_time = cleaned_data.get('date_time')
        employee = cleaned_data.get('employee')
        warehouse = cleaned_data.get('warehouse')
        instance = self.instance

        # Проверка на будущие даты
        if date_time and date_time > timezone.now():
            raise forms.ValidationError('Нельзя создавать записи на будущее время')

        # Проверка, что сотрудник действительно привязан к выбранному складу
        if employee and warehouse and employee.warehouse_id != warehouse.id:
            raise forms.ValidationError(
                f'Сотрудник {employee.short_name} не привязан к складу "{warehouse.name}"'
            )

        # Проверка на дубликаты записей для сотрудника в один день (исключая текущую)
        if date_time and employee:
            existing_record = WorkTimeRecord.objects.filter(
                employee=employee,
                date_time__date=date_time.date()
            ).exclude(id=instance.id).exists()

            if existing_record:
                raise forms.ValidationError(
                    f'Для сотрудника {employee.short_name} уже есть запись на {date_time.date()}'
                )

        return cleaned_data


class WorkTimeRecordFilterForm(forms.Form):
    """Форма для фильтрации записей рабочего времени"""

    date_from = forms.DateField(
        label='Дата с',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control auto-submit',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        label='Дата по',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control auto-submit',
            'type': 'date'
        })
    )
    employee = forms.ModelChoiceField(
        label='Сотрудник',
        required=False,
        queryset=Employee.get_active_employees(),
        widget=forms.Select(attrs={
            'class': 'form-control auto-submit'
        })
    )
    warehouse = forms.ModelChoiceField(
        label='Склад',
        required=False,
        queryset=Warehouse.get_active_warehouses(),
        widget=forms.Select(attrs={
            'class': 'form-control auto-submit'
        })
    )

    search = forms.CharField(
        label='Поиск по тексту',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по сотруднику или складу...'
        })
    )