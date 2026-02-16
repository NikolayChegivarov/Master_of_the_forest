from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from Forest_apps.employees.models import Employee


class CustomLoginForm(forms.Form):
    """Форма входа с выбором сотрудника из списка руководящих должностей"""

    employee = forms.ModelChoiceField(
        queryset=None,
        label='Сотрудник',
        empty_label="--- Выберите себя из списка ---",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'employee-select'
        })
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'password-input'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Сначала получим все руководящие должности для отладки
        руководящие_должности = [
            'руководитель',
            'бухгалтер',
            'механик',
            'мастер леса',
            'мастер ЛПЦ',
            'мастер ДОЦ',
            'мастер ЖД'
        ]

        # Для отладки - выведем все должности в консоль
        from Forest_apps.core.models import Position
        print("=== ВСЕ ДОЛЖНОСТИ В БД ===")
        for pos in Position.objects.all():
            print(f"ID: {pos.id}, Название: '{pos.name}', Активна: {pos.is_active}")

        print("=== СОТРУДНИКИ С РУКОВОДЯЩИМИ ДОЛЖНОСТЯМИ ===")
        employees = Employee.objects.filter(
            is_active=True,
            position__name__in=руководящие_должности
        ).select_related('position')

        for emp in employees:
            print(f"Сотрудник: {emp.last_name} {emp.first_name}, Должность: '{emp.position.name}'")

        # Фильтруем только руководящие должности
        self.fields['employee'].queryset = Employee.objects.filter(
            is_active=True,
            position__name__in=руководящие_должности
        ).select_related('position').order_by('position__name', 'last_name', 'first_name')

    def clean(self):
        cleaned_data = super().clean()
        employee = cleaned_data.get('employee')
        password = cleaned_data.get('password')

        if employee and password:
            username = f"employee_{employee.id}"

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                # Создаем пользователя при первом входе
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    first_name=employee.first_name,
                    last_name=employee.last_name,
                    email=f"{employee.id}@forest.local"
                )

            auth_user = authenticate(
                request=self.request,
                username=username,
                password=password
            )

            if auth_user is None:
                raise forms.ValidationError('Неверный пароль')

            cleaned_data['user'] = auth_user
            cleaned_data['employee_obj'] = employee

        return cleaned_data