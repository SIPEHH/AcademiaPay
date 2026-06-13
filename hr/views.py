from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from .models import Departement, Position, KpiCriteria, Employee, PenilaianKinerja, DetailPenilaian
from .forms import DepartementForm, PositionForm, KpiCriteriaForm
import json
from .models import Payroll, PayrollDetail

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        u, p = request.POST.get('username'), request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Username atau password salah!')
    return render(request, 'hr/login.html')

@login_required(login_url='login')
def dashboard_view(request):
    # 1. Dapatkan Bulan dan Tahun Saat Ini
    now = timezone.now()
    current_month = now.month
    current_year = now.year

    # 2. Hitung Total Karyawan
    total_karyawan = Employee.objects.count()

    # 3. Cari Data Gaji yang SUDAH SELESAI bulan ini
    payrolls_bulan_ini = Payroll.objects.filter(bulan=current_month, tahun=current_year, status='Selesai')
    
    # 4. Kalkulasi Angka untuk Dashboard
    total_sudah_digaji = payrolls_bulan_ini.count()
    total_belum_digaji = total_karyawan - total_sudah_digaji
    
    # Total uang gaji yang dikeluarkan bulan ini
    estimasi_gaji = payrolls_bulan_ini.aggregate(Sum('gaji_bersih'))['gaji_bersih__sum'] or 0
    
    # Hitung Persentase (Cegah error pembagian dengan nol)
    persentase_terbayar = 0
    if total_karyawan > 0:
        persentase_terbayar = int((total_sudah_digaji / total_karyawan) * 100)

    # 5. Dapatkan Daftar Karyawan yang BELUM DIGAJI
    # Ambil ID karyawan yang sudah ada di daftar gaji bulan ini
    paid_employee_ids = payrolls_bulan_ini.values_list('employee_id', flat=True)
    # Filter karyawan yang ID-nya TIDAK ADA di daftar tersebut (Batasi 5 orang saja untuk di tabel)
    karyawan_belum_digaji = Employee.objects.exclude(id__in=paid_employee_ids)[:5]

    context = {
        'total_karyawan': total_karyawan,
        'estimasi_gaji': estimasi_gaji,
        'total_sudah_digaji': total_sudah_digaji,
        'total_belum_digaji': total_belum_digaji,
        'persentase_terbayar': persentase_terbayar,
        'karyawan_belum_digaji': karyawan_belum_digaji,
    }
    return render(request, 'hr/dashboard.html', context)

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def master_data_view(request):
    if request.method == 'POST':
        if 'btn_tambah_departemen' in request.POST:
            nama = request.POST.get('nama_departemen')
            if Departement.objects.filter(nama_departemen__iexact=nama).exists():
                messages.error(request, 'Departemen sudah ada!')
            else:
                Departement.objects.create(nama_departemen=nama)
                messages.success(request, 'Departemen ditambah!')
            return redirect('master_data')
            
        elif 'btn_edit_departemen' in request.POST:
            dept = get_object_or_404(Departement, id=request.POST.get('dept_id'))
            nama = request.POST.get('edit_nama_departemen')
            if Departement.objects.filter(nama_departemen__iexact=nama).exclude(id=dept.id).exists():
                messages.error(request, 'Nama departemen duplikat!')
            else:
                dept.nama_departemen = nama
                dept.save()
                messages.success(request, 'Departemen berhasil diperbarui!')
            return redirect('master_data')
            
        elif 'btn_hapus_departemen' in request.POST:
            get_object_or_404(Departement, id=request.POST.get('dept_id')).delete()
            messages.success(request, 'Departemen berhasil dihapus!')
            return redirect('master_data')

        elif 'btn_tambah_jabatan' in request.POST:
            form = PositionForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Jabatan berhasil ditambahkan!')
            return redirect('master_data')
            
        elif 'btn_edit_jabatan' in request.POST:
            pos = get_object_or_404(Position, id=request.POST.get('pos_id'))
            pos.nama_jabatan = request.POST.get('edit_nama_jabatan')
            pos.departement_id = request.POST.get('edit_departement')
            pos.tunjangan_jabatan = request.POST.get('edit_tunjangan')
            pos.save()
            messages.success(request, 'Jabatan berhasil diperbarui!')
            return redirect('master_data')
            
        elif 'btn_hapus_jabatan' in request.POST:
            get_object_or_404(Position, id=request.POST.get('pos_id')).delete()
            messages.success(request, 'Jabatan berhasil dihapus!')
            return redirect('master_data')

    context = {
        'departements': Departement.objects.all(),
        'positions': Position.objects.all(),
        'dept_form': DepartementForm(),
        'pos_form': PositionForm(),
    }
    return render(request, 'hr/master_data.html', context)

@login_required(login_url='login')
def kelola_kpi_view(request, position_id):
    position = get_object_or_404(Position, id=position_id)
    
    def check_bobot(new_val, jenis_integrasi, exclude_id=None):
        kpis = KpiCriteria.objects.filter(position=position, integrasi_kpi=jenis_integrasi)
        if exclude_id: 
            kpis = kpis.exclude(id=exclude_id)
        
        total = float(kpis.aggregate(Sum('bobot'))['bobot__sum'] or 0)
        return (total + float(new_val)) <= 100

    if request.method == 'POST':
        if 'btn_tambah_kpi' in request.POST:
            nama = request.POST.get('nama_kriteria')
            bobot = request.POST.get('bobot')
            jenis_integrasi = request.POST.get('integrasi_kpi') 
            
            if KpiCriteria.objects.filter(position=position, nama_kriteria__iexact=nama).exists():
                messages.error(request, 'Nama KPI duplikat!')
            elif not check_bobot(bobot, jenis_integrasi): 
                messages.error(request, f'Total bobot untuk integrasi {jenis_integrasi} melebihi 100%!')
            else:
                KpiCriteria.objects.create(
                    position=position, 
                    nama_kriteria=nama, 
                    deskripsi=request.POST.get('deskripsi'), 
                    metode_ukur=request.POST.get('metode_ukur'),
                    integrasi_kpi=jenis_integrasi, 
                    bobot=bobot
                )
                messages.success(request, 'Indikator KPI berhasil ditambahkan!')
            return redirect('kelola_kpi', position_id=position.id)

        elif 'btn_edit_kpi' in request.POST:
            kpi = get_object_or_404(KpiCriteria, id=request.POST.get('kpi_id'))
            nama = request.POST.get('edit_nama_kriteria')
            bobot = request.POST.get('edit_bobot')
            jenis_integrasi = request.POST.get('edit_integrasi_kpi') 
            
            if KpiCriteria.objects.filter(position=position, nama_kriteria__iexact=nama).exclude(id=kpi.id).exists():
                messages.error(request, 'Nama KPI duplikat!')
            elif not check_bobot(bobot, jenis_integrasi, exclude_id=kpi.id): 
                messages.error(request, f'Total bobot untuk integrasi {jenis_integrasi} melebihi 100%!')
            else:
                kpi.nama_kriteria = nama
                kpi.bobot = bobot
                kpi.deskripsi = request.POST.get('edit_deskripsi')
                kpi.metode_ukur = request.POST.get('edit_metode_ukur')
                kpi.integrasi_kpi = jenis_integrasi
                kpi.save()
                messages.success(request, 'Indikator KPI berhasil diperbarui!')
            return redirect('kelola_kpi', position_id=position.id)
            
        elif 'btn_hapus_kpi' in request.POST:
            get_object_or_404(KpiCriteria, id=request.POST.get('kpi_id')).delete()
            messages.success(request, 'Indikator KPI berhasil dihapus!')
            return redirect('kelola_kpi', position_id=position.id)

    return render(request, 'hr/kelola_kpi.html', {
        'position': position,
        'kpi_list': KpiCriteria.objects.filter(position=position),
        'form': KpiCriteriaForm()
    })

@login_required(login_url='login')
def karyawan_view(request):
    if request.method == 'POST':
        if 'btn_tambah_karyawan' in request.POST:
            niy = request.POST.get('niy')
            if Employee.objects.filter(niy=niy).exists():
                messages.error(request, 'NIY sudah terdaftar!')
            else:
                Employee.objects.create(
                    niy=niy,
                    nama=request.POST.get('nama'),
                    position_id=request.POST.get('position'),
                    alamat=request.POST.get('alamat'),
                    no_hp=request.POST.get('no_hp'),
                    tanggal_masuk=request.POST.get('tanggal_masuk'),
                    status_karyawan=request.POST.get('status_karyawan'),
                    gaji_pokok=request.POST.get('gaji_pokok', 0) 
                )
                messages.success(request, 'Data karyawan berhasil ditambahkan!')
            return redirect('karyawan')
            
        elif 'btn_edit_karyawan' in request.POST:
            emp_id = request.POST.get('emp_id')
            niy = request.POST.get('edit_niy')
            
            emp = get_object_or_404(Employee, id=emp_id)
            if Employee.objects.filter(niy=niy).exclude(id=emp_id).exists():
                messages.error(request, 'NIY sudah digunakan karyawan lain!')
            else:
                emp.niy = niy
                emp.nama = request.POST.get('edit_nama')
                emp.position_id = request.POST.get('edit_position')
                emp.alamat = request.POST.get('edit_alamat')
                emp.no_hp = request.POST.get('edit_no_hp')
                emp.tanggal_masuk = request.POST.get('edit_tanggal_masuk')
                emp.status_karyawan = request.POST.get('edit_status_karyawan')
                emp.gaji_pokok = request.POST.get('edit_gaji_pokok', 0) 
                emp.save()
                messages.success(request, 'Data karyawan berhasil diperbarui!')
            return redirect('karyawan')
            
        elif 'btn_hapus_karyawan' in request.POST:
            emp_id = request.POST.get('emp_id')
            get_object_or_404(Employee, id=emp_id).delete()
            messages.success(request, 'Data karyawan berhasil dihapus!')
            return redirect('karyawan')

    employees = Employee.objects.all()
    search_query = request.GET.get('q', '')
    dept_filter = request.GET.get('dept', '')
    status_filter = request.GET.get('status', '')

    if search_query:
        employees = employees.filter(Q(nama__icontains=search_query) | Q(niy__icontains=search_query))
    if dept_filter:
        employees = employees.filter(position__departement_id=dept_filter)
    if status_filter:
        employees = employees.filter(status_karyawan=status_filter)

    context = {
        'employees': employees,
        'positions': Position.objects.all(),
        'departements': Departement.objects.all(),
        'status_choices': Employee.STATUS_CHOICES,
        'search_query': search_query,
        'dept_filter': dept_filter,
        'status_filter': status_filter,
    }
    return render(request, 'hr/karyawan.html', context)

@login_required(login_url='login')
def performance_tracker_view(request):
    now = timezone.now()
    selected_bulan = int(request.GET.get('bulan', now.month))
    selected_tahun = int(request.GET.get('tahun', now.year))
    search_query = request.GET.get('q', '')

    # ================= LOGIKA POST (SIMPAN & HAPUS NILAI) =================
    if request.method == 'POST':
        if 'btn_simpan_nilai' in request.POST:
            emp_id = request.POST.get('emp_id')
            emp = get_object_or_404(Employee, id=emp_id)
            kpis = KpiCriteria.objects.filter(position=emp.position)
            
            penilaian, _ = PenilaianKinerja.objects.get_or_create(
                employee=emp, bulan=selected_bulan, tahun=selected_tahun
            )
            
            # --- LOGIKA BARU: MENGHITUNG RATA-RATA INTEGRASI ---
            integrasi_totals = {}
            for kpi in kpis:
                skor_mentah = float(request.POST.get(f'kpi_{kpi.id}', 0))
                skor_berbobot = (skor_mentah * float(kpi.bobot)) / 100
                
                # Masukkan ke keranjang integrasi masing-masing
                if kpi.integrasi_kpi not in integrasi_totals:
                    integrasi_totals[kpi.integrasi_kpi] = 0
                integrasi_totals[kpi.integrasi_kpi] += skor_berbobot
                
                DetailPenilaian.objects.update_or_create(
                    penilaian=penilaian,
                    kriteria_kpi=kpi,
                    defaults={'skor_mentah': skor_mentah, 'skor_berbobot': skor_berbobot}
                )
            
            # Hitung total akhir: rata-rata dari semua kategori integrasi
            total_skor_akhir = 0
            if integrasi_totals:
                total_skor_akhir = sum(integrasi_totals.values()) / len(integrasi_totals)
            
            penilaian.total_skor = total_skor_akhir
            penilaian.save() # Ini otomatis men-trigger penentuan Grade A/B/C/D
            messages.success(request, f'Penilaian KPI {emp.nama} berhasil disimpan!')
            
        elif 'btn_hapus_nilai' in request.POST:
            PenilaianKinerja.objects.filter(id=request.POST.get('penilaian_id')).delete()
            messages.success(request, 'Data penilaian berhasil dihapus!')
            
        return redirect(f"{request.path}?bulan={selected_bulan}&tahun={selected_tahun}&q={search_query}")

    # ================= QUERY DATA FRONTEND =================
    employees = Employee.objects.all()
    if search_query:
        employees = employees.filter(Q(nama__icontains=search_query) | Q(niy__icontains=search_query))

    # Strukturkan data untuk Tabel & Modal
    emp_data = []
    for emp in employees:
        penilaian = PenilaianKinerja.objects.filter(employee=emp, bulan=selected_bulan, tahun=selected_tahun).first()
        kpis = KpiCriteria.objects.filter(position=emp.position).order_by('integrasi_kpi')
        
        kpi_grouped = {}
        for kpi in kpis:
            skor_mentah = 0
            if penilaian:
                detail = DetailPenilaian.objects.filter(penilaian=penilaian, kriteria_kpi=kpi).first()
                if detail: skor_mentah = detail.skor_mentah
            
            integ = kpi.integrasi_kpi
            if integ not in kpi_grouped:
                kpi_grouped[integ] = {'kpis': [], 'total_bobot_max': 0}
                
            kpi_grouped[integ]['kpis'].append({'kpi': kpi, 'skor_mentah': skor_mentah})
            kpi_grouped[integ]['total_bobot_max'] += kpi.bobot
            
        emp_data.append({
            'employee': emp,
            'penilaian': penilaian,
            'kpi_grouped': kpi_grouped, 
            'has_kpi': kpis.exists()
        })

    # ================= ANALITIK 3 CARD =================
    semua_penilaian_bulan_ini = PenilaianKinerja.objects.filter(bulan=selected_bulan, tahun=selected_tahun)
    
    # 1. Distribusi (Chart)
    distribusi = {
        'A': semua_penilaian_bulan_ini.filter(grade_akhir='A').count(),
        'B': semua_penilaian_bulan_ini.filter(grade_akhir='B').count(),
        'C': semua_penilaian_bulan_ini.filter(grade_akhir='C').count(),
        'D': semua_penilaian_bulan_ini.filter(grade_akhir='D').count(),
    }
    
    # 2 & 3. Rata-rata Bulan Ini vs Bulan Lalu
    avg_bulan_ini = semua_penilaian_bulan_ini.aggregate(Sum('total_skor'))['total_skor__sum'] or 0
    jml_dinilai = semua_penilaian_bulan_ini.count()
    avg_score = round(float(avg_bulan_ini) / jml_dinilai, 1) if jml_dinilai > 0 else 0

    bulan_lalu = selected_bulan - 1 if selected_bulan > 1 else 12
    tahun_lalu = selected_tahun if selected_bulan > 1 else selected_tahun - 1
    penilaian_lalu = PenilaianKinerja.objects.filter(bulan=bulan_lalu, tahun=tahun_lalu)
    avg_lalu_sum = penilaian_lalu.aggregate(Sum('total_skor'))['total_skor__sum'] or 0
    jml_lalu = penilaian_lalu.count()
    avg_score_lalu = round(float(avg_lalu_sum) / jml_lalu, 1) if jml_lalu > 0 else 0
    
    peningkatan = round(avg_score - avg_score_lalu, 1)

    context = {
        'emp_data': emp_data,
        'selected_bulan': selected_bulan,
        'selected_tahun': selected_tahun,
        'search_query': search_query,
        'bulan_choices': PenilaianKinerja.BULAN_CHOICES,
        'distribusi': distribusi,
        'avg_score': avg_score,
        'peningkatan': peningkatan,
    }
    return render(request, 'hr/performance_tracker.html', context)

@login_required(login_url='login')
def perhitungan_gaji_view(request):
    now = timezone.now()
    selected_bulan = int(request.GET.get('bulan', now.month))
    selected_tahun = int(request.GET.get('tahun', now.year))
    search_query = request.GET.get('q', '')
    status_filter = request.GET.get('status', 'semua') # semua, selesai, draft

    # ================= LOGIKA PENYIMPANAN (POST) =================
    if request.method == 'POST':
        if 'btn_simpan_gaji' in request.POST:
            emp_id = request.POST.get('emp_id')
            emp = get_object_or_404(Employee, id=emp_id)
            
            hari_alpa = int(request.POST.get('hari_alpa', 0))
            potongan_alpa = hari_alpa * 25000
            
            # Ambil data Gaji Pokok & Tunjangan saat ini dari Master
            gaji_pokok = emp.gaji_pokok
            tunjangan = emp.position.tunjangan_jabatan if emp.position else 0
            
            # Menghitung Bonus
            bonus_names = request.POST.getlist('bonus_nama[]')
            bonus_nominals = request.POST.getlist('bonus_nominal[]')
            total_bonus = sum([int(nom.replace('.', '') or 0) for nom in bonus_nominals])
            
            # Perhitungan Gaji Bersih
            gaji_bersih = (gaji_pokok + tunjangan) - potongan_alpa + total_bonus
            
            # Simpan ke Database
            payroll, created = Payroll.objects.update_or_create(
                employee=emp, bulan=selected_bulan, tahun=selected_tahun,
                defaults={
                    'gaji_pokok': gaji_pokok,
                    'tunjangan_jabatan': tunjangan,
                    'hari_alpa': hari_alpa,
                    'total_potongan': potongan_alpa,
                    'total_bonus': total_bonus,
                    'gaji_bersih': gaji_bersih,
                    'status': 'Selesai' 
                }
            )
            
            # Hapus bonus lama dan simpan yang baru (update relasi)
            payroll.bonus_details.all().delete()
            for nama, nom in zip(bonus_names, bonus_nominals):
                nominal_bersih = int(nom.replace('.', '') or 0)
                if nama and nominal_bersih > 0:
                    PayrollDetail.objects.create(payroll=payroll, nama_bonus=nama, nominal=nominal_bersih)
            
            messages.success(request, f'Gaji {emp.nama} berhasil dihitung dan disimpan!')
            return redirect(f"{request.path}?bulan={selected_bulan}&tahun={selected_tahun}&q={search_query}&status={status_filter}")

    # ================= QUERY DATA KARYAWAN & GAJI =================
    employees = Employee.objects.all()
    if search_query:
        employees = employees.filter(Q(nama__icontains=search_query) | Q(niy__icontains=search_query))

    data_gaji = []
    total_diproses = 0
    estimasi_pencairan = 0

    for emp in employees:
        # Cari apakah gaji bulan ini sudah dibuat
        payroll = Payroll.objects.filter(employee=emp, bulan=selected_bulan, tahun=selected_tahun).first()
        
        # Jika belum ada di database, buat data 'bayangan' untuk ditampilkan di tabel
        status = payroll.status if payroll else 'Draft'
        gaji_pokok = payroll.gaji_pokok if payroll else emp.gaji_pokok
        tunjangan = payroll.tunjangan_jabatan if payroll else (emp.position.tunjangan_jabatan if emp.position else 0)
        
        if status == 'Selesai':
            total_diproses += 1
            estimasi_pencairan += payroll.gaji_bersih
            
        # Terapkan Filter Status
        if status_filter == 'selesai' and status != 'Selesai': continue
        if status_filter == 'draft' and status != 'Draft': continue

        # Format detail bonus untuk dikirim ke JS Modal
        bonus_list = []
        if payroll:
            bonus_list = [{'nama': b.nama_bonus, 'nominal': float(b.nominal)} for b in payroll.bonus_details.all()]

        data_gaji.append({
            'employee': emp,
            'payroll': payroll,
            'status': status,
            'pendapatan_tetap': gaji_pokok + tunjangan,
            'gaji_pokok': gaji_pokok,
            'tunjangan': tunjangan,
            'hari_alpa': payroll.hari_alpa if payroll else 0,
            'total_bonus': payroll.total_bonus if payroll else 0,
            'gaji_bersih': payroll.gaji_bersih if payroll else (gaji_pokok + tunjangan),
            'bonus_json': json.dumps(bonus_list) # Kirim data bonus format JSON untuk JS
        })

    total_karyawan = employees.count()
    belum_dihitung = total_karyawan - total_diproses

    context = {
        'data_gaji': data_gaji,
        'total_diproses': total_diproses,
        'total_karyawan': total_karyawan,
        'belum_dihitung': belum_dihitung,
        'estimasi_pencairan': estimasi_pencairan,
        'selected_bulan': selected_bulan,
        'selected_tahun': selected_tahun,
        'search_query': search_query,
        'status_filter': status_filter,
        'bulan_choices': Payroll.BULAN_CHOICES,
    }
    return render(request, 'hr/perhitungan_gaji.html', context)

