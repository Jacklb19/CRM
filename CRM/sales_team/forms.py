from django import forms
from .models import TeamMember


class TeamMemberForm(forms.ModelForm):
    class Meta:
        model = TeamMember
        fields = ['department', 'phone', 'hire_date', 'is_active_seller']
        widgets = {
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Ventas B2B'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+57 300 123 4567'}),
            'hire_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active_seller': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
