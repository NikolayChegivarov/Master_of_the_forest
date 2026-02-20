from django import forms
from Forest_apps.core.models import Counterparty


class CounterpartyCreateForm(forms.ModelForm):
    """Форма создания контрагента"""

    class Meta:
        model = Counterparty
        fields = ['legal_form', 'name', 'inn', 'ogrn']
        widgets = {
            'legal_form': forms.Select(attrs={
                'class': 'form-control',
                'autofocus': True
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите наименование'
            }),
            'inn': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите ИНН (10 или 12 цифр)'
            }),
            'ogrn': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите ОГРН (13 или 15 цифр)'
            }),
        }
        labels = {
            'legal_form': 'Организационно-правовая форма',
            'name': 'Наименование',
            'inn': 'ИНН',
            'ogrn': 'ОГРН',
        }

    def clean_inn(self):
        """Валидация ИНН"""
        inn = self.cleaned_data['inn'].strip()

        # Проверка длины ИНН
        if len(inn) not in [10, 12]:
            raise forms.ValidationError('ИНН должен содержать 10 или 12 цифр')

        # Проверка, что ИНН состоит только из цифр
        if not inn.isdigit():
            raise forms.ValidationError('ИНН должен содержать только цифры')

        # Проверка на уникальность
        if Counterparty.objects.filter(inn=inn, is_active=True).exists():
            raise forms.ValidationError('Контрагент с таким ИНН уже существует')

        return inn

    def clean_ogrn(self):
        """Валидация ОГРН"""
        ogrn = self.cleaned_data['ogrn'].strip()

        # Проверка длины ОГРН
        if len(ogrn) not in [13, 15]:
            raise forms.ValidationError('ОГРН должен содержать 13 или 15 цифр')

        # Проверка, что ОГРН состоит только из цифр
        if not ogrn.isdigit():
            raise forms.ValidationError('ОГРН должен содержать только цифры')

        # Проверка на уникальность
        if Counterparty.objects.filter(ogrn=ogrn, is_active=True).exists():
            raise forms.ValidationError('Контрагент с таким ОГРН уже существует')

        return ogrn

    def clean(self):
        """Дополнительная валидация"""
        cleaned_data = super().clean()
        legal_form = cleaned_data.get('legal_form')
        inn = cleaned_data.get('inn')
        ogrn = cleaned_data.get('ogrn')

        # Проверка соответствия длины ИНН и ОГРН организационно-правовой форме
        if legal_form and inn and ogrn:
            if legal_form == 'ООО':
                if len(inn) != 10:
                    self.add_error('inn', 'Для ООО ИНН должен содержать 10 цифр')
                if len(ogrn) != 13:
                    self.add_error('ogrn', 'Для ООО ОГРН должен содержать 13 цифр')
            elif legal_form == 'ИП':
                if len(inn) != 12:
                    self.add_error('inn', 'Для ИП ИНН должен содержать 12 цифр')
                if len(ogrn) != 15:
                    self.add_error('ogrn', 'Для ИП ОГРН должен содержать 15 цифр')

        return cleaned_data


class CounterpartyEditForm(forms.ModelForm):
    """Форма редактирования контрагента"""

    class Meta:
        model = Counterparty
        fields = ['legal_form', 'name', 'inn', 'ogrn']
        widgets = {
            'legal_form': forms.Select(attrs={
                'class': 'form-control',
                'autofocus': True
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите наименование'
            }),
            'inn': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите ИНН'
            }),
            'ogrn': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите ОГРН'
            }),
        }
        labels = {
            'legal_form': 'Организационно-правовая форма',
            'name': 'Наименование',
            'inn': 'ИНН',
            'ogrn': 'ОГРН',
        }

    def clean_inn(self):
        """Валидация ИНН"""
        inn = self.cleaned_data['inn'].strip()
        instance = self.instance

        # Проверка длины ИНН
        if len(inn) not in [10, 12]:
            raise forms.ValidationError('ИНН должен содержать 10 или 12 цифр')

        # Проверка, что ИНН состоит только из цифр
        if not inn.isdigit():
            raise forms.ValidationError('ИНН должен содержать только цифры')

        # Проверка на уникальность (исключая текущего контрагента)
        if Counterparty.objects.filter(inn=inn, is_active=True).exclude(id=instance.id).exists():
            raise forms.ValidationError('Контрагент с таким ИНН уже существует')

        return inn

    def clean_ogrn(self):
        """Валидация ОГРН"""
        ogrn = self.cleaned_data['ogrn'].strip()
        instance = self.instance

        # Проверка длины ОГРН
        if len(ogrn) not in [13, 15]:
            raise forms.ValidationError('ОГРН должен содержать 13 или 15 цифр')

        # Проверка, что ОГРН состоит только из цифр
        if not ogrn.isdigit():
            raise forms.ValidationError('ОГРН должен содержать только цифры')

        # Проверка на уникальность (исключая текущего контрагента)
        if Counterparty.objects.filter(ogrn=ogrn, is_active=True).exclude(id=instance.id).exists():
            raise forms.ValidationError('Контрагент с таким ОГРН уже существует')

        return ogrn

    def clean(self):
        """Дополнительная валидация"""
        cleaned_data = super().clean()
        legal_form = cleaned_data.get('legal_form')
        inn = cleaned_data.get('inn')
        ogrn = cleaned_data.get('ogrn')

        # Проверка соответствия длины ИНН и ОГРН организационно-правовой форме
        if legal_form and inn and ogrn:
            if legal_form == 'ООО':
                if len(inn) != 10:
                    self.add_error('inn', 'Для ООО ИНН должен содержать 10 цифр')
                if len(ogrn) != 13:
                    self.add_error('ogrn', 'Для ООО ОГРН должен содержать 13 цифр')
            elif legal_form == 'ИП':
                if len(inn) != 12:
                    self.add_error('inn', 'Для ИП ИНН должен содержать 12 цифр')
                if len(ogrn) != 15:
                    self.add_error('ogrn', 'Для ИП ОГРН должен содержать 15 цифр')

        return cleaned_data