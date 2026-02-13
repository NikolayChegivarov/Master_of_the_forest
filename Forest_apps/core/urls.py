# Forest_apps/core/urls.py
from django.urls import path
from .views import auth_views, management

app_name = 'core'

urlpatterns = [
    # Аутентификация
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('', auth_views.dashboard, name='dashboard'),

    # Панели управления руководящего состава
    path('supervisor/', management.supervisor_dashboard, name='supervisor_dashboard'),
    path('booker/', management.booker_dashboard, name='booker_dashboard'),
    path('mechanic/', management.mechanic_dashboard, name='mechanic_dashboard'),
    path('master/lpc/', management.master_lpc_dashboard, name='master_lpc_dashboard'),
    path('master/doc/', management.master_doc_dashboard, name='master_doc_dashboard'),
    path('master/railways/', management.master_railways_dashboard, name='master_railways_dashboard'),
]