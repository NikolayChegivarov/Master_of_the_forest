from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def supervisor_dashboard(request):
    """Панель руководителя"""
    context = {
        'title': 'Панель руководителя',
        'employee_name': request.session.get('employee_name'),
        'position': request.session.get('position_name'),
    }
    return render(request, 'Management/supervisor.html', context)

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