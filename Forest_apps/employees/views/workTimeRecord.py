from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta
from Forest_apps.employees.models import WorkTimeRecord, Employee
from Forest_apps.core.models import Warehouse, Position
from Forest_apps.employees.forms.workTimeRecord import (
    WorkTimeRecordCreateForm,
    WorkTimeRecordEditForm,
    WorkTimeRecordFilterForm
)


@login_required
def worktime_list_view(request):
    """Страница со списком записей рабочего времени (только для должности пользователя)"""

    # Получаем должность текущего пользователя из сессии
    user_position_name = request.session.get('position_name')
    user_position_id = None

    # Находим ID должности по названию
    try:
        position = Position.objects.get(name__iexact=user_position_name)
        user_position_id = position.id
    except Position.DoesNotExist:
        user_position_id = -1

    # Базовый запрос - только записи, созданные этой должностью
    records = WorkTimeRecord.objects.filter(
        created_by_position_id=user_position_id
    ).select_related(
        'warehouse', 'employee', 'employee__position', 'created_by', 'created_by_position'
    ).order_by('-date_time')

    # Фильтрация
    filter_form = WorkTimeRecordFilterForm(request.GET or None)

    if filter_form.is_valid():
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        employee = filter_form.cleaned_data.get('employee')
        warehouse = filter_form.cleaned_data.get('warehouse')
        search = filter_form.cleaned_data.get('search')

        if date_from:
            records = records.filter(date_time__date__gte=date_from)
        if date_to:
            records = records.filter(date_time__date__lte=date_to)
        if employee:
            records = records.filter(employee=employee)
        if warehouse:
            records = records.filter(warehouse=warehouse)
        if search:
            records = records.filter(
                Q(employee__last_name__icontains=search) |
                Q(employee__first_name__icontains=search) |
                Q(warehouse__name__icontains=search)
            )

    # Подсчет итогов
    total_hours = records.aggregate(total=Sum('hours'))['total'] or 0

    # Статистика за сегодня
    today = timezone.now().date()
    today_records = WorkTimeRecord.objects.filter(
        created_by_position_id=user_position_id,
        date_time__date=today
    ).select_related('employee', 'warehouse')
    today_hours = today_records.aggregate(total=Sum('hours'))['total'] or 0
    today_employees = today_records.values('employee').distinct().count()

    context = {
        'title': 'Учет рабочего времени',
        'employee_name': request.session.get('employee_name'),
        'position_name': user_position_name,
        'records': records,
        'filter_form': filter_form,
        'total_hours': total_hours,
        'today_hours': today_hours,
        'today_employees': today_employees,
        'today': today,
    }
    return render(request, 'WorkTimeRecord/worktime_list.html', context)


@login_required
def worktime_create_view(request):
    """Создание новой записи рабочего времени"""

    # Получаем должность пользователя из сессии
    user_position = request.session.get('position_name')

    if request.method == 'POST':
        form = WorkTimeRecordCreateForm(
            request.POST,
            user=request.user,
            user_position=user_position  # ПЕРЕДАЕМ ДОЛЖНОСТЬ В ФОРМУ
        )
        if form.is_valid():
            # Сохраняем запись
            record = form.save(commit=False)

            # Добавляем создателя (пользователя)
            record.created_by = request.user

            # Добавляем должность создателя
            position_name = request.session.get('position_name')
            try:
                position = Position.objects.get(name__iexact=position_name)
                record.created_by_position = position
            except Position.DoesNotExist:
                # Если должность не найдена, создаем
                position, _ = Position.objects.get_or_create(
                    name=position_name,
                    defaults={'is_active': True}
                )
                record.created_by_position = position

            record.save()

            messages.success(
                request,
                f'Запись для {record.employee.short_name} на {record.date_time.date()} успешно создана!'
            )

            return redirect('employees:worktime_list')
    else:
        form = WorkTimeRecordCreateForm(
            user=request.user,
            user_position=user_position  # ПЕРЕДАЕМ ДОЛЖНОСТЬ В ФОРМУ
        )

    context = {
        'title': 'Добавление записи',
        'form': form,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'WorkTimeRecord/worktime_create.html', context)


@login_required
def worktime_edit_view(request, record_id):
    """Редактирование записи рабочего времени (только для своей должности)"""

    # Получаем должность текущего пользователя
    user_position = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=user_position)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('employees:worktime_list')

    # Получаем запись по ID и проверяем, что она создана этой должностью
    record = get_object_or_404(
        WorkTimeRecord,
        id=record_id,
        created_by_position=position
    )

    if request.method == 'POST':
        form = WorkTimeRecordEditForm(
            request.POST,
            instance=record,
            user=request.user,
            user_position=user_position  # ПЕРЕДАЕМ ДОЛЖНОСТЬ В ФОРМУ
        )
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Запись для {record.employee.short_name} на {record.date_time.date()} успешно обновлена!'
            )
            return redirect('employees:worktime_list')
    else:
        form = WorkTimeRecordEditForm(
            instance=record,
            user=request.user,
            user_position=user_position  # ПЕРЕДАЕМ ДОЛЖНОСТЬ В ФОРМУ
        )

    context = {
        'title': 'Редактирование записи',
        'form': form,
        'record': record,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'WorkTimeRecord/worktime_edit.html', context)


@login_required
def worktime_delete_view(request, record_id):
    """Удаление записи рабочего времени (только для своей должности)"""

    # Получаем должность текущего пользователя
    position_name = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('employees:worktime_list')

    try:
        # Проверяем, что запись создана этой должностью
        record = get_object_or_404(
            WorkTimeRecord,
            id=record_id,
            created_by_position=position
        )
        employee_name = record.employee.short_name
        record_date = record.date_time.date()
        record.delete()
        messages.success(
            request,
            f'Запись для {employee_name} на {record_date} удалена!'
        )
    except Exception as e:
        messages.error(request, str(e))

    return redirect('employees:worktime_list')


@login_required
def worktime_employee_report_view(request, employee_id):
    """Отчет по сотруднику за период (только для своей должности)"""

    # Получаем должность текущего пользователя
    position_name = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('employees:worktime_list')

    employee = get_object_or_404(Employee, id=employee_id)

    # Период по умолчанию: последние 30 дней
    date_to = timezone.now().date()
    date_from = date_to - timedelta(days=30)

    # Получаем параметры из запроса
    date_from_str = request.GET.get('date_from', date_from.strftime('%Y-%m-%d'))
    date_to_str = request.GET.get('date_to', date_to.strftime('%Y-%m-%d'))

    try:
        date_from = timezone.datetime.strptime(date_from_str, '%Y-%m-%d').date()
    except:
        date_from = timezone.now().date() - timedelta(days=30)

    try:
        date_to = timezone.datetime.strptime(date_to_str, '%Y-%m-%d').date()
    except:
        date_to = timezone.now().date()

    # Получаем записи за период (только созданные текущей должностью)
    records = WorkTimeRecord.objects.filter(
        employee=employee,
        created_by_position=position,
        date_time__date__gte=date_from,
        date_time__date__lte=date_to
    ).select_related('warehouse', 'created_by', 'created_by_position').order_by('date_time')

    # Группировка по дням
    daily_stats = []
    current_date = date_from
    while current_date <= date_to:
        day_records = records.filter(date_time__date=current_date)
        day_hours = day_records.aggregate(total=Sum('hours'))['total'] or 0

        daily_stats.append({
            'date': current_date,
            'hours': day_hours,
            'records': day_records
        })

        current_date += timedelta(days=1)

    # Итоги
    total_hours = records.aggregate(total=Sum('hours'))['total'] or 0
    avg_hours = total_hours / ((date_to - date_from).days + 1) if (date_to - date_from).days >= 0 else 0

    context = {
        'title': f'Отчет: {employee.short_name}',
        'employee_name': request.session.get('employee_name'),
        'position_name': position_name,
        'employee': employee,
        'records': records,
        'daily_stats': daily_stats,
        'date_from': date_from,
        'date_to': date_to,
        'total_hours': total_hours,
        'avg_hours': avg_hours,
        'days_count': (date_to - date_from).days + 1,
    }

    return render(request, 'WorkTimeRecord/worktime_employee_report.html', context)


@login_required
def worktime_warehouse_report_view(request, warehouse_id):
    """Отчет по складу за период (только для своей должности)"""

    # Получаем должность текущего пользователя
    position_name = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('employees:worktime_list')

    warehouse = get_object_or_404(Warehouse, id=warehouse_id)

    # Период по умолчанию: текущий месяц
    today = timezone.now().date()
    date_from = today.replace(day=1)
    date_to = today

    # Получаем параметры из запроса
    date_from_str = request.GET.get('date_from', date_from.strftime('%Y-%m-%d'))
    date_to_str = request.GET.get('date_to', date_to.strftime('%Y-%m-%d'))

    try:
        date_from = timezone.datetime.strptime(date_from_str, '%Y-%m-%d').date()
    except:
        date_from = today.replace(day=1)

    try:
        date_to = timezone.datetime.strptime(date_to_str, '%Y-%m-%d').date()
    except:
        date_to = today

    # Получаем записи за период (только созданные текущей должностью)
    records = WorkTimeRecord.objects.filter(
        warehouse=warehouse,
        created_by_position=position,
        date_time__date__gte=date_from,
        date_time__date__lte=date_to
    ).select_related('employee', 'employee__position', 'created_by', 'created_by_position').order_by('date_time',
                                                                                                     'employee__last_name')

    # Группировка по сотрудникам
    employee_stats = []
    employees = records.values('employee').distinct()

    for emp_data in employees:
        emp_id = emp_data['employee']
        if emp_id:
            emp_records = records.filter(employee_id=emp_id)
            emp = emp_records.first().employee if emp_records.exists() else None

            if emp:
                emp_hours = emp_records.aggregate(total=Sum('hours'))['total'] or 0
                employee_stats.append({
                    'employee': emp,
                    'hours': emp_hours,
                    'records_count': emp_records.count(),
                    'records': emp_records
                })

    # Итоги
    total_hours = records.aggregate(total=Sum('hours'))['total'] or 0
    avg_daily_hours = total_hours / ((date_to - date_from).days + 1) if (date_to - date_from).days >= 0 else 0

    context = {
        'title': f'Отчет по складу: {warehouse.name}',
        'employee_name': request.session.get('employee_name'),
        'position_name': position_name,
        'warehouse': warehouse,
        'records': records,
        'employee_stats': employee_stats,
        'date_from': date_from,
        'date_to': date_to,
        'total_hours': total_hours,
        'avg_daily_hours': avg_daily_hours,
        'days_count': (date_to - date_from).days + 1,
    }

    return render(request, 'WorkTimeRecord/worktime_warehouse_report.html', context)