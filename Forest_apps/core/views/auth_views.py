from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse

from Forest_apps.core.forms.auth_forms import CustomLoginForm


def login_view(request):
    """Страница входа с выбором сотрудника"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        form.request = request
        if form.is_valid():
            user = form.cleaned_data['user']
            employee = form.cleaned_data['employee_obj']

            login(request, user)

            # Сохраняем данные сотрудника в сессии
            request.session['employee_id'] = employee.id
            request.session['employee_name'] = employee.full_name
            request.session['position_name'] = employee.position.name

            messages.success(
                request,
                f'Добро пожаловать, {employee.full_name}!'
            )

            # Перенаправление в зависимости от должности
            position_name = employee.position.name.lower()

            if position_name == 'руководитель':
                return redirect('core:supervisor_dashboard')
            elif position_name == 'бухгалтер':
                return redirect('core:booker_dashboard')
            elif position_name == 'механик':
                return redirect('core:mechanic_dashboard')
            elif position_name == 'мастер лпц':
                return redirect('core:master_lpc_dashboard')
            elif position_name == 'мастер доц':
                return redirect('core:master_doc_dashboard')
            elif position_name == 'мастер жд':
                return redirect('core:master_railways_dashboard')
            else:
                return redirect('core:dashboard')
    else:
        form = CustomLoginForm()

    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('core:login')


@login_required
def dashboard(request):
    """Перенаправление на соответствующую панель"""
    position_name = request.session.get('position_name', '').lower()

    if position_name == 'руководитель':
        return redirect('core:supervisor_dashboard')
    elif position_name == 'бухгалтер':
        return redirect('core:booker_dashboard')
    elif position_name == 'механик':
        return redirect('core:mechanic_dashboard')
    elif position_name == 'мастер лпц':
        return redirect('core:master_lpc_dashboard')
    elif position_name == 'мастер доц':
        return redirect('core:master_doc_dashboard')
    elif position_name == 'мастер жд':
        return redirect('core:master_railways_dashboard')
    else:
        messages.warning(request, 'У вас нет доступа к панели управления')
        return redirect('core:login')