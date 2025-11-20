from django import forms
from customers.models import Customer
from django.contrib.auth.models import User
from datetime import datetime, timedelta


class ReportFilterForm(forms.Form):
    REPORT_CHOICES = [
        ('', 'Selecciona un tipo de reporte'),
        ('sales', '📊 Reporte de Ventas'),
        ('customers', '👥 Reporte de Clientes'),
        ('sellers', '🎯 Análisis de Vendedores'),
        ('followups', '💬 Reporte de Seguimientos'),
        ('opportunities', '📈 Reporte de Oportunidades'),
        ('pipeline', '🔄 Análisis de Pipeline'),
    ]
    
    EXPORT_CHOICES = [
        ('', 'Sin exportar'),
        ('excel', '📥 Exportar a Excel'),
        ('pdf', '📄 Exportar a PDF'),
    ]
    
    report_type = forms.ChoiceField(
        choices=REPORT_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Cliente (Opcional)'
    )
    
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role='vendedor'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Vendedor (Opcional)'
    )
    
    opportunity_status = forms.MultipleChoiceField(
        choices=[
            ('abierta', 'Abierta'),
            ('calificada', 'Calificada'),
            ('propuesta', 'Propuesta'),
            ('negociacion', 'Negociación'),
            ('ganada', 'Ganada'),
            ('perdida', 'Perdida'),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        label='Estados de Oportunidad'
    )
    
    export_format = forms.ChoiceField(
        choices=EXPORT_CHOICES,
        required=False,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Exportar'
    )
