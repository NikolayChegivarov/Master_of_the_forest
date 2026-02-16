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
        # Фильтруем только руководящие должности
        руководящие_должности = [
            'Руководитель',
            'Бухгалтер',
            'Механик',
            'Мастер ЛПЦ',
            'Мастер ДОЦ',
            'Мастер ЖД'
        ]

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