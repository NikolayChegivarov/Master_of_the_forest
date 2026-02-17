from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def logging_site_view(request):
    """Страница управления лесосеками"""
    context = {
        'title': 'Лесосека',
        'employee_name': request.session.get('employee_name'),
    }
    return render(request, 'logging_site/logging_site.html', context)