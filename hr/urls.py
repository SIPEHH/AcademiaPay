from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('', views.login_view),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('master-data/', views.master_data_view, name='master_data'), 
    path('master-data/kpi/<int:position_id>/', views.kelola_kpi_view, name='kelola_kpi'),
    path('karyawan/', views.karyawan_view, name='karyawan'),
    path('performance-tracker/', views.performance_tracker_view, name='performance_tracker'),
    path('logout/', views.logout_view, name='logout'),
    path('perhitungan-gaji/', views.perhitungan_gaji_view, name='perhitungan_gaji'),
]