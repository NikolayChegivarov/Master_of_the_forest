# Forest_apps/core/views/management.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

# Представление для панели руководителя
def supervisor_dashboard(request):
    """
    Панель управления руководителя
    """
    return render(request, 'Management/supervisor.html')

# Заглушки для остальных страниц (пока просто возвращаем текст)
def employees_list(request):
    return HttpResponse("Список сотрудников - в разработке")

def counterparties_list(request):
    return HttpResponse("Список контрагентов - в разработке")

def external_interfaces(request):
    return HttpResponse("Сторонние интерфейсы - в разработке")