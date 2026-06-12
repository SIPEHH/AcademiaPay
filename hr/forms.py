from django import forms
from .models import Departement, Position, KpiCriteria

class DepartementForm(forms.ModelForm):
    class Meta:
        model = Departement
        fields = ['nama_departemen']
        widgets = {
            'nama_departemen': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 
                'required': True,
                'placeholder': 'Masukkan nama departemen...'
            })
        }

class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ['nama_jabatan', 'departement', 'tunjangan_jabatan']
        widgets = {
            'nama_jabatan': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'required': True}),
            'departement': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'required': True}),
            'tunjangan_jabatan': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'required': True}),
        }

class KpiCriteriaForm(forms.ModelForm):
    class Meta:
        model = KpiCriteria
        fields = ['nama_kriteria', 'deskripsi', 'metode_ukur', 'integrasi_kpi', 'bobot']
        widgets = {
            'nama_kriteria': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500', 'required': True}),
            'deskripsi': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500', 'rows': 2}),
            'metode_ukur': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500'}),
            'integrasi_kpi': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500'}),
            'bobot': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500', 'required': True, 'step': '0.01', 'placeholder': 'Maksimal 100'}),
        }