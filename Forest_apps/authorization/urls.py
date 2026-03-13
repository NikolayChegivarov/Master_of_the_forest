# Forest_apps.authorization.urls
from django.urls import path

from Forest_apps.authorization.views.booker_views import booker_balances_view, booker_movements_view
from Forest_apps.authorization.views.login import login_view, logout_view
from Forest_apps.authorization.views.management_dashboards import (
    supervisor_dashboard, booker_dashboard, mechanic_dashboard,
    master_lpc_dashboard, master_doc_dashboard, master_railways_dashboard, master_forest_dashboard,
    third_party_interfaces_view, switch_to_position_view, return_to_original_position_view
)

app_name = 'authorization'  # 👈 ИЗМЕНЕНО с auth на authorization

urlpatterns = [
    # === АВТОРИЗАЦИЯ ===
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('', login_view, name='root'),

    # === ПАНЕЛИ УПРАВЛЕНИЯ ===
    path('supervisor/', supervisor_dashboard, name='supervisor_dashboard'),
    path('booker/', booker_dashboard, name='booker_dashboard'),
    path('master/forest/', master_forest_dashboard, name='master_forest_dashboard'),
    path('mechanic/', mechanic_dashboard, name='mechanic_dashboard'),
    path('master/lpc/', master_lpc_dashboard, name='master_lpc_dashboard'),
    path('master/doc/', master_doc_dashboard, name='master_doc_dashboard'),
    path('master/railways/', master_railways_dashboard, name='master_railways_dashboard'),

    # === СТОРОННИЕ ИНТЕРФЕЙСЫ ===
    path('third-party/', third_party_interfaces_view, name='third_party_interfaces'),
    path('switch-to/<str:position_name>/', switch_to_position_view, name='switch_to_position'),
    path('return-to-original/', return_to_original_position_view, name='return_to_original'),

    # === БУХГАЛТЕР ===
    path('booker/balances/', booker_balances_view, name='booker_balances'),
    path('booker/movements/', booker_movements_view, name='booker_movements'),
]