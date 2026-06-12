from django.db import models
from django.contrib.auth.models import AbstractUser

# 1. Tabel USERS 
class User(AbstractUser):
    ROLE_CHOICES = (
        ('superadmin', 'Superadmin'),
        ('biro_keuangan', 'Biro Keuangan'),
        ('biro_sdm', 'Biro SDM'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.username} ({self.role})"

# 2. Tabel DEPARTEMENTS
class Departement(models.Model):
    nama_departemen = models.CharField(max_length=255)

    def __str__(self):
        return self.nama_departemen

# 3. Tabel POSITIONS (Jabatan)
class Position(models.Model):
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE, related_name='positions')
    nama_jabatan = models.CharField(max_length=255)
    gaji_pokok = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    tunjangan_jabatan = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    def __str__(self):
        return self.nama_jabatan

# 4. Tabel EMPLOYEES (Karyawan)
class Employee(models.Model):
    STATUS_CHOICES = [
        ('Tetap', 'Karyawan Tetap'),
        ('Kontrak', 'Karyawan Kontrak'),
        ('Percobaan', 'Masa Percobaan (Probation)'),
    ]

    niy = models.CharField(max_length=50, unique=True)
    nama = models.CharField(max_length=100)
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='employees')
    alamat = models.TextField(blank=True, null=True)
    no_hp = models.CharField(max_length=20, blank=True, null=True)
    tanggal_masuk = models.DateField()
    status_karyawan = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Tetap')
    # === TAMBAHAN BARU: GAJI POKOK ===
    gaji_pokok = models.DecimalField(max_digits=12, decimal_places=0, default=0)

    def __str__(self):
        return f"{self.niy} - {self.nama}"
# 5. Tabel PERIODS (Periode Penggajian & KPI)
class Period(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('closed', 'Closed'),
    )
    nama_periode = models.CharField(max_length=50) # Contoh: "Juni 2026"
    tanggal_mulai = models.DateField()
    tanggal_selesai = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')

    def __str__(self):
        return self.nama_periode

# 6. Tabel KPI_CRITERIA (Kriteria KPI Jabatan)
class KpiCriteria(models.Model):
    UKUR_CHOICES = (
        ('persentase', 'Persentase'),
        ('boolean', 'Sudah/Belum'),
    )
    INTEGRASI_CHOICES = (
        ('performance', 'Performance'),
        ('jabatan', 'Jabatan'),
    )
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='kpi_criteria')
    nama_kriteria = models.CharField(max_length=255)
    deskripsi = models.TextField(blank=True, null=True)
    metode_ukur = models.CharField(max_length=20, choices=UKUR_CHOICES)
    integrasi_kpi = models.CharField(max_length=20, choices=INTEGRASI_CHOICES)
    bobot = models.DecimalField(max_digits=5, decimal_places=2) # Maksimal 100.00

    def __str__(self):
        return self.nama_kriteria

# 7. Tabel DISCIPLINE_ASSESSMENTS (Penilaian Kedisiplinan)
class DisciplineAssessment(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='discipline_assessments')
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    skor_kedisiplinan = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Disiplin {self.employee.nama} - {self.period.nama_periode}"

# 8. Tabel KPI_ASSESSMENTS (Penilaian KPI per Karyawan)
class KpiAssessment(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='kpi_assessments')
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    kpi_criteria = models.ForeignKey(KpiCriteria, on_delete=models.CASCADE)
    nilai = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def __str__(self):
        return f"KPI {self.kpi_criteria.nama_kriteria} - {self.employee.nama}"

# 9. Tabel SALARY_COMPONENTS (Master Data Komponen Gaji/Potongan)
class SalaryComponent(models.Model):
    TIPE_CHOICES = (
        ('tunjangan', 'Tunjangan'),
        ('potongan', 'Potongan'),
    )
    nama_komponen = models.CharField(max_length=255)
    tipe = models.CharField(max_length=20, choices=TIPE_CHOICES)
    nilai_default = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.nama_komponen} ({self.tipe})"

# 10. Tabel PAYROLLS (Transaksi Penggajian)
class Payroll(models.Model):
    STATUS_PAYROLL_CHOICES = (
        ('draft', 'Draft'),
        ('belum', 'Belum (Belum Dibayar)'),
        ('done', 'Done (Sudah Dibayar)'),
    )
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payrolls')
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    gaji_pokok = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_tunjangan = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_potongan = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    gaji_bersih = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_PAYROLL_CHOICES, default='draft')

    def __str__(self):
        return f"Payroll {self.employee.nama} - {self.period.nama_periode}"

# 11. Tabel PAYROLL_DETAILS (Rincian Tunjangan/Potongan pada suatu Payroll)
class PayrollDetail(models.Model):
    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE, related_name='details')
    salary_component = models.ForeignKey(SalaryComponent, on_delete=models.CASCADE)
    nominal = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Detail {self.salary_component.nama_komponen} - Payroll ID: {self.payroll.id}"

class PenilaianKinerja(models.Model):
    BULAN_CHOICES = [
        (1, 'Januari'), (2, 'Februari'), (3, 'Maret'), (4, 'April'),
        (5, 'Mei'), (6, 'Juni'), (7, 'Juli'), (8, 'Agustus'),
        (9, 'September'), (10, 'Oktober'), (11, 'November'), (12, 'Desember')
    ]
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Final', 'Final (Terkunci)'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='riwayat_penilaian')
    bulan = models.IntegerField(choices=BULAN_CHOICES)
    tahun = models.IntegerField()
    total_skor = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    tanggal_dinilai = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Mencegah 1 karyawan dinilai 2 kali di bulan dan tahun yang sama
        unique_together = ('employee', 'bulan', 'tahun') 

    def __str__(self):
        return f"Penilaian {self.employee.nama} - {self.get_bulan_display()} {self.tahun}"


class DetailPenilaian(models.Model):
    penilaian = models.ForeignKey(PenilaianKinerja, on_delete=models.CASCADE, related_name='details')
    kriteria_kpi = models.ForeignKey(KpiCriteria, on_delete=models.CASCADE)
    skor_mentah = models.DecimalField(max_digits=5, decimal_places=2, default=0) # Input HR (contoh: 80)
    skor_berbobot = models.DecimalField(max_digits=5, decimal_places=2, default=0) # Hasil (contoh: 80 * 20% = 16)

    def save(self, *args, **kwargs):
        # Otomatis menghitung skor berbobot sebelum disimpan ke database
        self.skor_berbobot = (self.skor_mentah * self.kriteria_kpi.bobot) / 100
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.penilaian.employee.nama} - {self.kriteria_kpi.nama_kriteria}"
    
class PenilaianKinerja(models.Model):
    BULAN_CHOICES = [
        (1, 'Januari'), (2, 'Februari'), (3, 'Maret'), (4, 'April'),
        (5, 'Mei'), (6, 'Juni'), (7, 'Juli'), (8, 'Agustus'),
        (9, 'September'), (10, 'Oktober'), (11, 'November'), (12, 'Desember')
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='riwayat_penilaian')
    bulan = models.IntegerField(choices=BULAN_CHOICES)
    tahun = models.IntegerField()
    total_skor = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    grade_akhir = models.CharField(max_length=2, blank=True, null=True)
    tanggal_dinilai = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'bulan', 'tahun')

    def tentukan_grade(self):
        if self.total_skor >= 85: return 'A'
        elif self.total_skor >= 70: return 'B'
        elif self.total_skor >= 55: return 'C'
        else: return 'D'

    def save(self, *args, **kwargs):
        self.grade_akhir = self.tentukan_grade()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.nama} - {self.get_bulan_display()} {self.tahun}"


class DetailPenilaian(models.Model):
    penilaian = models.ForeignKey(PenilaianKinerja, on_delete=models.CASCADE, related_name='details')
    kriteria_kpi = models.ForeignKey('KpiCriteria', on_delete=models.CASCADE)
    skor_mentah = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    skor_berbobot = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.skor_berbobot = (float(self.skor_mentah) * float(self.kriteria_kpi.bobot)) / 100
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.penilaian.employee.nama} - {self.kriteria_kpi.nama_kriteria}"