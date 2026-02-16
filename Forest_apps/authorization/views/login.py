from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from Forest_apps.authorization.forms import CustomLoginForm


def login_view(request):
    """Страница входа с выбором сотрудника"""
    # Если пользователь уже авторизован - редиректим на его панель
    if request.user.is_authenticated:
        position_name = request.session.get('position_name', '').lower()

        if position_name == 'руководитель':
            return redirect('authorization:supervisor_dashboard')
        elif position_name == 'бухгалтер':
            return redirect('authorization:booker_dashboard')
        elif position_name == 'механик':
            return redirect('authorization:mechanic_dashboard')
        elif 'мастер лпц' in position_name:
            return redirect('authorization:master_lpc_dashboard')
        elif 'мастер доц' in position_name:
            return redirect('authorization:master_doc_dashboard')
        elif 'мастер жд' in position_name:
            return redirect('authorization:master_railways_dashboard')

    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        form.request = request
        if form.is_valid():
            user = form.cleaned_data['user']
            employee = form.cleaned_data['employee_obj']

            login(request, user)

            request.session['employee_id'] = employee.id
            request.session['employee_name'] = employee.full_name
            request.session['position_name'] = employee.position.name

            messages.success(request, f'Добро пожаловать, {employee.full_name}!')

            position_name = employee.position.name.lower()

            if position_name == 'руководитель':
                return redirect('authorization:supervisor_dashboard')
            elif position_name == 'бухгалтер':
                return redirect('authorization:booker_dashboard')
            elif position_name == 'механик':
                return redirect('authorization:mechanic_dashboard')
            elif 'мастер лпц' in position_name:
                return redirect('authorization:master_lpc_dashboard')
            elif 'мастер доц' in position_name:
                return redirect('authorization:master_doc_dashboard')
            elif 'мастер жд' in position_name:
                return redirect('authorization:master_railways_dashboard')
    else:
        form = CustomLoginForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('authorization:login')