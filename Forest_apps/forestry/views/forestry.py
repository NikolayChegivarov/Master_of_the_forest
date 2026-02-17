from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def forestry_view(request):
    """Страница управления лесничествами"""
    context = {
        'title': 'Лесничества',
        'employee_name': request.session.get('employee_name'),
    }
    return render(request, 'forestry.html', context)