from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from Forest_apps.forestry.forms.create_forestry import ForestryCreateForm
from Forest_apps.forestry.models import Forestry


@login_required
def forestry_view(request):
    """Страница управления лесничествами"""

    # Получаем все активные лесничества
    active_forestries = Forestry.get_active_forestries()  # 👈 Добавьте эту строку

    context = {
        'title': 'Лесничества',
        'employee_name': request.session.get('employee_name'),
        'forestries': active_forestries,  # 👈 Передаем в шаблон
    }
    return render(request, 'forestry/forestry.html', context)


@login_required
def create_forestry_view(request):
    """Создание нового лесничества"""

    if request.method == 'POST':
        form = ForestryCreateForm(request.POST)
        if form.is_valid():
            # Сохраняем лесничество
            forestry = form.save()

            # Добавляем сообщение об успехе
            messages.success(
                request,
                f'Лесничество "{forestry.name}" успешно создано!'
            )

            # Перенаправляем на страницу со списком лесничеств
            return redirect('forestry:forestry')
    else:
        form = ForestryCreateForm()

    context = {
        'title': 'Создание лесничества',
        'form': form,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'forestry/create_forestry.html', context)