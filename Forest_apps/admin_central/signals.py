from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from Forest_apps.employees.models import Employee


@receiver(post_save, sender=Employee)
def sync_employee_user(sender, instance, created, **kwargs):
    """Синхронизирует данные сотрудника с пользователем Django"""

    руководящие_должности = [
        'Руководитель', 'Бухгалтер', 'Механик',
        'Мастер ЛПЦ', 'Мастер ДОЦ', 'Мастер ЖД'
    ]

    # Проверяем, должна ли эта должность иметь доступ
    should_have_access = (instance.position and
                          instance.position.name in руководящие_должности and
                          instance.is_active)

    username = f"employee_{instance.id}"

    try:
        user = User.objects.get(username=username)

        if should_have_access:
            # Обновляем данные пользователя
            user.first_name = instance.first_name
            user.last_name = instance.last_name
            user.is_active = instance.is_active
            user.is_staff = True
            user.save()
        else:
            # Если должность больше не руководящая - удаляем доступ
            user.is_staff = False
            user.is_active = False
            user.save()

    except User.DoesNotExist:
        if should_have_access and instance.password:
            # Создаем нового пользователя
            User.objects.create_user(
                username=username,
                password=instance.password,  # Пароль уже хеширован в модели
                first_name=instance.first_name,
                last_name=instance.last_name,
                email=f"{instance.id}@forest.local",
                is_staff=True,
                is_active=instance.is_active
            )