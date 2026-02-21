from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta
from Forest_apps.employees.models import WorkTimeRecord, Employee
from Forest_apps.core.models import Warehouse
from Forest_apps.employees.forms.workTimeRecord import (
    WorkTimeRecordCreateForm,
    WorkTimeRecordEditForm,
    WorkTimeRecordFilterForm
)


@login_required
def worktime_list_view(request):
    """Страница со списком записей рабочего времени"""

    # Базовый запрос
    records = WorkTimeRecord.objects.select_related(
        'warehouse', 'employee', 'employee__position', 'created_by'
    ).order_by('-date_time')

    # Фильтрация
    filter_form = WorkTimeRecordFilterForm(request.GET or None)

    if filter_form.is_valid():
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        employee = filter_form.cleaned_data.get('employee')
        warehouse = filter_form.cleaned_data.get('warehouse')

        if date_from:
            records = records.filter(date_time__date__gte=date_from)
        if date_to:
            records = records.filter(date_time__date__lte=date_to)
        if employee:
            records = records.filter(employee=employee)
        if warehouse:
            records = records.filter(warehouse=warehouse)

    # Поиск по тексту
    search_query = request.GET.get('search', '')
    if search_query:
        records = records.filter(
            Q(employee__last_name__icontains=search_query) |
            Q(employee__first_name__icontains=search_query) |
            Q(warehouse__name__icontains=search_query)
        )

    # Подсчет итогов
    total_hours = records.aggregate(total=Sum('hours'))['total'] or 0

    # Статистика за сегодня
    today = timezone.now().date()
    today_records = WorkTimeRecord.objects.filter(
        date_time__date=today
    ).select_related('employee', 'warehouse')
    today_hours = today_records.aggregate(total=Sum('hours'))['total'] or 0
    today_employees = today_records.values('employee').distinct().count()

    context = {
        'title': 'Учет рабочего времени',
        'employee_name': request.session.get('employee_name'),
        'records': records,
        'filter_form': filter_form,
        'search_query': search_query,
        'total_hours': total_hours,
        'today_hours': today_hours,
        'today_employees': today_employees,
        'today': today,
    }
    return render(request, 'WorkTimeRecord/worktime_list.html', context)


@login_required
def worktime_create_view(request):
    """Создание новой записи рабочего времени"""

    if request.method == 'POST':
        form = WorkTimeRecordCreateForm(request.POST)
        if form.is_valid():
            # Сохраняем запись, но пока не коммитим
            record = form.save(commit=False)
            # Добавляем создателя
            record.created_by = request.user
            # Сохраняем
            record.save()

            messages.success(
                request,
                f'Запись для {record.employee.short_name} на {record.date_time.date()} успешно создана!'
            )

            return redirect('employees:worktime_list')
    else:
        form = WorkTimeRecordCreateForm()

    context = {
        'title': 'Добавление записи',
        'form': form,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'WorkTimeRecord/worktime_create.html', context)


@login_required
def worktime_edit_view(request, record_id):
    """Редактирование записи рабочего времени"""

    # Получаем запись по ID или возвращаем 404
    record = get_object_or_404(WorkTimeRecord, id=record_id)

    if request.method == 'POST':
        form = WorkTimeRecordEditForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Запись для {record.employee.short_name} на {record.date_time.date()} успешно обновлена!'
            )
            return redirect('employees:worktime_list')
    else:
        form = WorkTimeRecordEditForm(instance=record)

    context = {
        'title': 'Редактирование записи',
        'form': form,
        'record': record,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'WorkTimeRecord/worktime_edit.html', context)


@login_required
def worktime_delete_view(request, record_id):
    """Удаление записи рабочего времени (полное удаление из БД)"""

    try:
        record = get_object_or_404(WorkTimeRecord, id=record_id)
        employee_name = record.employee.short_name
        record_date = record.date_time.date()
        record.delete()  # 👈 Полное удаление из БД
        messages.success(
            request,
            f'Запись для {employee_name} на {record_date} удалена!'
        )
    except Exception as e:
        messages.error(request, str(e))

    return redirect('employees:worktime_list')


@login_required
def worktime_employee_report_view(request, employee_id):
    """Отчет по сотруднику за период"""

    employee = get_object_or_404(Employee, id=employee_id)

    # Период по умолчанию: последние 30 дней
    date_to = timezone.now().date()
    date_from = date_to - timedelta(days=30)

    # Получаем параметры из запроса
    date_from_str = request.GET.get('date_from', date_from.strftime('%Y-%m-%d'))
    date_to_str = request.GET.get('date_to', date_to.strftime('%Y-%m-%d'))

    # Преобразуем строки в даты
    try:
        date_from = timezone.datetime.strptime(date_from_str, '%Y-%m-%d').date()
    except:
        date_from = timezone.now().date() - timedelta(days=30)

    try:
        date_to = timezone.datetime.strptime(date_to_str, '%Y-%m-%d').date()
    except:
        date_to = timezone.now().date()

    # Получаем записи за период
    records = WorkTimeRecord.objects.filter(
        employee=employee,
        date_time__date__gte=date_from,
        date_time__date__lte=date_to,
        is_active=True
    ).select_related('warehouse', 'created_by').order_by('date_time')

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
    """Отчет по складу за период"""

    warehouse = get_object_or_404(Warehouse, id=warehouse_id)

    # Период по умолчанию: текущий месяц
    today = timezone.now().date()
    date_from = today.replace(day=1)
    date_to = today

    # Получаем параметры из запроса
    date_from_str = request.GET.get('date_from', date_from.strftime('%Y-%m-%d'))
    date_to_str = request.GET.get('date_to', date_to.strftime('%Y-%m-%d'))

    # Преобразуем строки в даты
    try:
        date_from = timezone.datetime.strptime(date_from_str, '%Y-%m-%d').date()
    except:
        date_from = today.replace(day=1)

    try:
        date_to = timezone.datetime.strptime(date_to_str, '%Y-%m-%d').date()
    except:
        date_to = today

    # Получаем записи за период
    records = WorkTimeRecord.objects.filter(
        warehouse=warehouse,
        date_time__date__gte=date_from,
        date_time__date__lte=date_to,
        is_active=True
    ).select_related('employee', 'employee__position', 'created_by').order_by('date_time', 'employee__last_name')

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