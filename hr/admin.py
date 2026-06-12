from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Departement, Position, Employee, Period, 
    KpiCriteria, DisciplineAssessment, KpiAssessment, 
    SalaryComponent, Payroll, PayrollDetail
)

# 1. Buat konfigurasi khusus agar kolom 'role' muncul
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Informasi Role', {'fields': ('role',)}),
    )

# 2. Daftarkan User menggunakan konfigurasi khusus tersebut (GANTI BARIS INI)
admin.site.register(User, CustomUserAdmin)

# Daftarkan tabel lainnya (tetap sama)
admin.site.register(Departement)
admin.site.register(Position)
admin.site.register(Employee)
admin.site.register(Period)
admin.site.register(KpiCriteria)
admin.site.register(DisciplineAssessment)
admin.site.register(KpiAssessment)
admin.site.register(SalaryComponent)
admin.site.register(Payroll)
admin.site.register(PayrollDetail)