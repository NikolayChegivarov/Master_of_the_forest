
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% РУКОВОДИТЕЛЬ %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
@login_required
def supervisor_dashboard(request):
    """Панель руководителя"""

    context = {
        'title': 'Панель руководителя',
        'employee_name': request.session.get('employee_name'),
        'position': request.session.get('position_name'),
        'user': request.user,  # Явно передаем user в контекст
    }
    return render(request, 'Management/supervisor.html', context)


@login_required
def third_party_interfaces_view(request):
    """Страница выбора интерфейсов руководящего состава"""
    context = {
        'title': 'Сторонние интерфейсы',
        'employee_name': request.session.get('employee_name'),
        'position': request.session.get('position_name'),
    }
    return render(request, 'third_party_interfaces.html', context)


@login_required
def switch_to_position_view(request, position_name):
    """
    Временное переключение на интерфейс другой должности.
    Сохраняем оригинальную должность в сессии и подменяем текущую.
    """
    # Проверяем, что текущий пользователь - руководитель
    current_position = request.session.get('position_name', '').lower()
    if current_position != 'руководитель':
        messages.error(request, 'У вас нет прав для доступа к этому разделу')
        return redirect('authorization:supervisor_dashboard')

    # Сохраняем оригинальную должность в сессии (если еще не сохранена)
    if 'original_position' not in request.session:
        request.session['original_position'] = {
            'name': request.session.get('position_name'),
            'id': request.session.get('position_id'),  # если есть
        }

    # Словарь соответствия названий должностей и URL-имен
    position_urls = {
        'бухгалтер': 'authorization:booker_dashboard',
        'механик': 'authorization:mechanic_dashboard',
        'мастер леса': 'authorization:master_forest_dashboard',
        'мастер лпц': 'authorization:master_lpc_dashboard',
        'мастер доц': 'authorization:master_doc_dashboard',
        'мастер жд': 'authorization:master_railways_dashboard',
    }

    # Проверяем, что запрошенная должность существует в словаре
    normalized_position = position_name.lower()
    if normalized_position not in position_urls:
        messages.error(request, f'Неизвестная должность: {position_name}')
        return redirect('authorization:third_party_interfaces')

    # Обновляем должность в сессии
    request.session['position_name'] = position_name  # Сохраняем как есть (с сохранением регистра)
    request.session['is_switched'] = True  # Флаг, что мы в режиме подмены

    messages.success(
        request,
        f'Вы вошли в интерфейс {position_name}. Для возврата к своему интерфейсу используйте кнопку "Вернуться".'
    )

    # Перенаправляем на соответствующий дашборд
    return redirect(position_urls[normalized_position])


@login_required
def return_to_original_position_view(request):
    """Возврат к оригинальной должности руководителя"""

    if 'original_position' in request.session:
        # Восстанавливаем оригинальную должность
        original = request.session['original_position']
        request.session['position_name'] = original['name']
        # Очищаем временные данные
        del request.session['original_position']
        request.session.pop('is_switched', None)

        messages.success(request, 'Вы вернулись в свой интерфейс руководителя.')
    else:
        messages.info(request, 'Вы уже находитесь в своем интерфейсе.')

    return redirect('authorization:supervisor_dashboard')

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% СТОРОННИЕ ИНТЕРФЕЙСЫ %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

@login_required
def booker_dashboard(request):
    """Панель бухгалтера"""
    context = {
        'title': 'Панель бухгалтера',
        'employee_name': request.session.get('employee_name'),
        'position': request.session.get('position_name'),
    }
    return render(request, 'Management/booker.html', context)

@login_required
def master_forest_dashboard(request):
    """Панель мастера леса"""
    context = {
        'title': 'Панель мастера леса',
        'employee_name': request.session.get('employee_name'),
        'position': request.session.get('position_name'),
    }
    return render(request, 'Management/master_Forest.html', context)

@login_required
def mechanic_dashboard(request):
    """Панель механика"""
    context = {
        'title': 'Панель механика',
        'employee_name': request.session.get('employee_name'),
        'position': request.session.get('position_name'),
    }
    return render(request, 'Management/mechanic.html', context)

@login_required
def master_lpc_dashboard(request):
    """Панель мастера ЛПЦ"""
    context = {
        'title': 'Панель мастера ЛПЦ',
        'employee_name': request.session.get('employee_name'),
        'position': request.session.get('position_name'),
    }
    return render(request, 'Management/master_LPC.html', context)

@login_required
def master_doc_dashboard(request):
    """Панель мастера ДОЦ"""
    context = {
        'title': 'Панель мастера ДОЦ',
        'employee_name': request.session.get('employee_name'),
        'position': request.session.get('position_name'),
    }
    return render(request, 'Management/master_DOC.html', context)

@login_required
def master_railways_dashboard(request):
    """Панель мастера ЖД"""
    context = {
        'title': 'Панель мастера ЖД',
        'employee_name': request.session.get('employee_name'),
        'position': request.session.get('position_name'),
    }
    return render(request, 'Management/master_Railways.html', context)