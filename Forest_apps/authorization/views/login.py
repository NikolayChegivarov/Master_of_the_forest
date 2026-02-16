from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from Forest_apps.authorization.forms import CustomLoginForm


def login_view(request):
    """Страница входа с выбором сотрудника"""
    # Если пользователь уже авторизован - редиректим на его панель
    if request.user.is_authenticated:
        position_name = request.session.get('position_name', '').lower()
        print(f"Already authenticated: {position_name}")  # Отладка

        if position_name == 'руководитель':
            return redirect('authorization:supervisor_dashboard')
        elif position_name == 'бухгалтер':
            return redirect('authorization:booker_dashboard')
        elif position_name == 'механик':
            return redirect('authorization:mechanic_dashboard')
        elif position_name == 'мастер лпц':
            return redirect('authorization:master_lpc_dashboard')
        elif position_name == 'мастер доц':
            return redirect('authorization:master_doc_dashboard')
        elif position_name == 'мастер жд':
            return redirect('authorization:master_railways_dashboard')
        elif position_name == 'мастер леса':
            return redirect('authorization:master_forest_dashboard')

    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        form.request = request
        if form.is_valid():
            user = form.cleaned_data['user']
            employee = form.cleaned_data['employee_obj']

            login(request, user)

            # Устанавливаем данные в сессию
            request.session['employee_id'] = employee.id
            request.session['employee_name'] = employee.full_name
            request.session['position_name'] = employee.position.name
            request.session.save()  # Принудительно сохраняем сессию

            print(f"Session after login: {request.session.items()}")  # Отладка

            messages.success(request, f'Добро пожаловать, {employee.full_name}!')

            position_name = employee.position.name.lower()

            if position_name == 'руководитель':
                return redirect('authorization:supervisor_dashboard')
            elif position_name == 'бухгалтер':
                return redirect('authorization:booker_dashboard')
            elif position_name == 'механик':
                return redirect('authorization:mechanic_dashboard')
            elif position_name == 'мастер лпц':
                return redirect('authorization:master_lpc_dashboard')
            elif position_name == 'мастер доц':
                return redirect('authorization:master_doc_dashboard')
            elif position_name == 'мастер жд':
                return redirect('authorization:master_railways_dashboard')
            elif position_name == 'мастер леса':
                return redirect('authorization:master_forest_dashboard')
            else:
                # Если должность не найдена, перенаправляем на страницу входа
                messages.error(request, 'Для вашей должности не настроена панель управления')
                return redirect('authorization:login')
    else:
        form = CustomLoginForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    """Выход из системы"""
    print(f"Logging out user: {request.user}")  # Отладка
    logout(request)
    request.session.flush()  # Полная очистка сессии
    messages.info(request, 'Вы вышли из системы')
    return redirect('authorization:login')