from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from Forest_apps.employees.models import Employee
from Forest_apps.employees.forms.employee import EmployeeCreateForm, EmployeeEditForm


@login_required
def employee_list_view(request):
    """Страница со списком сотрудников"""

    # Получаем все активные сотрудники с связанными данными
    active_employees = Employee.get_active_employees().select_related('position', 'warehouse', 'created_by')

    # Поиск по сотрудникам
    search_query = request.GET.get('search', '')
    if search_query:
        active_employees = active_employees.filter(
            Q(last_name__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(middle_name__icontains=search_query) |
            Q(position__name__icontains=search_query)
        )

    context = {
        'title': 'Сотрудники',
        'employee_name': request.session.get('employee_name'),
        'employees': active_employees,
        'search_query': search_query,
    }
    return render(request, 'Employee/employee_list.html', context)


@login_required
def employee_detail_view(request, employee_id):
    """Детальная информация о сотруднике"""

    employee = get_object_or_404(
        Employee.objects.select_related('position', 'warehouse', 'created_by'),
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
            # Сохраняем сотрудника, но пока не коммитим
            employee = form.save(commit=False)
            # Добавляем создателя
            employee.created_by = request.user
            # Сохраняем
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
    """Редактирование сотрудника"""

    # Получаем сотрудника по ID или возвращаем 404
    employee = get_object_or_404(Employee, id=employee_id)

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
    """Деактивация сотрудника"""

    try:
        # Используем метод из модели
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
    """Активация сотрудника (для администрирования)"""

    try:
        employee = get_object_or_404(Employee, id=employee_id)
        employee.is_active = True
        employee.save()
        messages.success(
            request,
            f'Сотрудник {employee.short_name} успешно активирован!'
        )
    except Exception as e:
        messages.error(request, str(e))

    return redirect('employees:employee_list')