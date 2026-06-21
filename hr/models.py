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
        ('Contrak', 'Karyawan Kontrak'),
        ('Percobaan', 'Masa Percobaan (Probation)'),
    ]

    niy = models.CharField(max_length=50, unique=True)
    nama = models.CharField(max_length=100)
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='employees')
    alamat = models.TextField(blank=True, null=True)
    no_hp = models.CharField(max_length=20, blank=True, null=True)
    tanggal_masuk = models.DateField()
    status_karyawan = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Tetap')
    gaji_pokok = models.DecimalField(max_digits=12, decimal_places=0, default=0)

    def __str__(self):
        return f"{self.niy} - {self.nama}"

# 5. Tabel MASTER TUNJANGAN (Konfigurasi Finansial Integrasi KPI)
class MasterTunjangan(models.Model):
    nama_tunjangan = models.CharField(max_length=100, unique=True)
    nominal_maksimal = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return self.nama_tunjangan

# 6. Tabel PERIODS (Periode Penggajian & KPI)
class Period(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('closed', 'Closed'),
    )
    nama_periode = models.CharField(max_length=50) 
    tanggal_mulai = models.DateField()
    tanggal_selesai = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')

    def __str__(self):
        return self.nama_periode

# 7. Tabel KPI_CRITERIA (Kriteria KPI Jabatan)
class KpiCriteria(models.Model):
    UKUR_CHOICES = (
        ('persentase', 'Persentase'),
        ('boolean', 'Sudah/Belum'),
    )
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='kpi_criteria')
    nama_kriteria = models.CharField(max_length=255)
    deskripsi = models.TextField(blank=True, null=True)
    metode_ukur = models.CharField(max_length=20, choices=UKUR_CHOICES)
    integrasi_kpi = models.CharField(max_length=100) 
    bobot = models.DecimalField(max_digits=5, decimal_places=2) 

    def __str__(self):
        return self.nama_kriteria

# 8. Tabel PAYROLLS (Transaksi Penggajian Terperbarui)
class Payroll(models.Model):
    BULAN_CHOICES = [
        (1, 'Januari'), (2, 'Februari'), (3, 'Maret'), (4, 'April'),
        (5, 'Mei'), (6, 'Juni'), (7, 'Juli'), (8, 'Agustus'),
        (9, 'September'), (10, 'Oktober'), (11, 'November'), (12, 'Desember')
    ]
    STATUS_CHOICES = (
        ('Draft', 'Draft'),
        ('Selesai', 'Selesai'),
    )
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payrolls')
    bulan = models.IntegerField(choices=BULAN_CHOICES)
    tahun = models.IntegerField()
    
    # Komponen Gaji Fisik
    gaji_pokok = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    tunjangan_jabatan = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    
    # Variabel Dinamis Hasil Olah KPI & Kebijakan Finansial
    total_bonus = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    total_potongan = models.DecimalField(max_digits=15, decimal_places=0, default=0) 
    deskripsi_potongan = models.TextField(blank=True, null=True) 
    
    # Hasil Akhir Remunerasi
    gaji_bersih = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')

    class Meta:
        unique_together = ('employee', 'bulan', 'tahun')

    def __str__(self):
        return f"Gaji {self.employee.nama} - {self.get_bulan_display()} {self.tahun}"


class PayrollDetail(models.Model):
    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE, related_name='bonus_details')
    nama_bonus = models.CharField(max_length=255) 
    nominal = models.DecimalField(max_digits=15, decimal_places=0, default=0)

    def __str__(self):
        return f"{self.nama_bonus} - Rp {self.nominal}"

# 9. Tabel PENILAIAN KPI (Hasil tracking bulanan - Struktur Bersih & Valid)
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
    kriteria_kpi = models.ForeignKey(KpiCriteria, on_delete=models.CASCADE)
    skor_mentah = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    skor_berbobot = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.skor_berbobot = (float(self.skor_mentah) * float(self.kriteria_kpi.bobot)) / 100
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.penilaian.employee.nama} - {self.kriteria_kpi.nama_kriteria}"

# ================= TABEL LEGACY (DIPERTAHANKAN AGAR RIWAYAT SEBELUMNYA TIDAK ERROR) =================
class DisciplineAssessment(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='discipline_assessments')
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    skor_kedisiplinan = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

class KpiAssessment(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='kpi_assessments')
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    kpi_criteria = models.ForeignKey(KpiCriteria, on_delete=models.CASCADE)
    nilai = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

class SalaryComponent(models.Model):
    nama_komponen = models.CharField(max_length=255)
    tipe = models.CharField(max_length=20)
    nilai_default = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)