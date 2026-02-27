from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from Forest_apps.employees.models import Employee
from Forest_apps.core.models import Position
from Forest_apps.employees.forms.employee import EmployeeCreateForm, EmployeeEditForm


@login_required
def employee_list_view(request):
    """Страница со списком сотрудников (только для должности пользователя)"""

    # Получаем должность текущего пользователя из сессии
    user_position_name = request.session.get('position_name')
    user_position_id = None

    # Находим ID должности по названию
    try:
        position = Position.objects.get(name__iexact=user_position_name)
        user_position_id = position.id
    except Position.DoesNotExist:
        # Если должность не найдена, показываем пустой список
        user_position_id = -1

    # Получаем сотрудников, созданных этой должностью
    employees = Employee.objects.filter(
        created_by_position_id=user_position_id
    ).select_related('position', 'warehouse', 'created_by_position').order_by('-created_at')

    # Поиск по сотрудникам
    search_query = request.GET.get('search', '')
    if search_query:
        employees = employees.filter(
            Q(last_name__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(middle_name__icontains=search_query) |
            Q(position__name__icontains=search_query)
        )

    context = {
        'title': 'Сотрудники',
        'employee_name': request.session.get('employee_name'),
        'position_name': user_position_name,
        'employees': employees,
        'search_query': search_query,
    }
    return render(request, 'Employee/employee_list.html', context)


@login_required
def employee_detail_view(request, employee_id):
    """Детальная информация о сотруднике"""

    employee = get_object_or_404(
        Employee.objects.select_related('position', 'warehouse', 'created_by', 'created_by_position'),
        id=employee_id
    )

    context = {
        'title': f'Сотрудник: {employee.short_name}',
        'employee_name': request.session.get('employee_name'),
        'employee': employee,
    }
    return render(request, 'Employee/employee_detail.html', context)


@login_required
def employee_create_view(request):
    """Создание нового сотрудника"""

    if request.method == 'POST':
        form = EmployeeCreateForm(request.POST)
        if form.is_valid():
            # Сохраняем сотрудника
            employee = form.save(commit=False)

            # Добавляем создателя (пользователя)
            employee.created_by = request.user

            # Добавляем должность создателя
            position_name = request.session.get('position_name')
            try:
                position = Position.objects.get(name__iexact=position_name)
                employee.created_by_position = position
            except Position.DoesNotExist:
                # Если должность не найдена, создаем
                position, _ = Position.objects.get_or_create(
                    name=position_name,
                    defaults={'is_active': True}
                )
                employee.created_by_position = position

            employee.save()

            messages.success(
                request,
                f'Сотрудник {employee.short_name} успешно создан!'
            )

            return redirect('employees:employee_list')
    else:
        form = EmployeeCreateForm()

    context = {
        'title': 'Создание сотрудника',
        'form': form,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'Employee/employee_create.html', context)


@login_required
def employee_edit_view(request, employee_id):
    """Редактирование сотрудника (только для своей должности)"""

    # Получаем должность текущего пользователя
    position_name = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('employees:employee_list')

    # Получаем сотрудника по ID и проверяем, что он создан этой должностью
    employee = get_object_or_404(
        Employee,
        id=employee_id,
        created_by_position=position
    )

    if request.method == 'POST':
        form = EmployeeEditForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Сотрудник {employee.short_name} успешно обновлен!'
            )
            return redirect('employees:employee_detail', employee_id=employee.id)
    else:
        form = EmployeeEditForm(instance=employee)

    context = {
        'title': f'Редактирование: {employee.short_name}',
        'form': form,
        'employee': employee,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'Employee/employee_edit.html', context)


@login_required
def employee_deactivate_view(request, employee_id):
    """Деактивация сотрудника (только для своей должности)"""

    # Получаем должность текущего пользователя
    position_name = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('employees:employee_list')

    try:
        # Проверяем, что сотрудник создан этой должностью
        employee = get_object_or_404(
            Employee,
            id=employee_id,
            created_by_position=position
        )
        employee = Employee.deactivate_employee(employee_id)
        messages.success(
            request,
            f'Сотрудник {employee.short_name} успешно деактивирован!'
        )
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('employees:employee_list')


@login_required
def employee_activate_view(request, employee_id):
    """Активация сотрудника (только для своей должности)"""

    # Получаем должность текущего пользователя
    position_name = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('employees:employee_list')

    try:
        # Проверяем, что сотрудник создан этой должностью
        employee = get_object_or_404(
            Employee,
            id=employee_id,
            created_by_position=position
        )
        employee.is_active = True
        employee.save()
        messages.success(
            request,
            f'Сотрудник {employee.short_name} успешно активирован!'
        )
    except Exception as e:
        messages.error(request, str(e))

    return redirect('employees:employee_list')