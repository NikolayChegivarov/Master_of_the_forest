from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def materials_view(request):
    """Страница управления материалами"""
    context = {
        'title': 'Материалы',
        'employee_name': request.session.get('employee_name'),
    }
    return render(request, 'materials.html', context)