from django import forms
from django.db.models import Q
from .models import Customer
from django.contrib.auth.models import User
from django import forms
from django.core.exceptions import ValidationError
from .models import Customer
import re


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone', 'company', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo del cliente'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@ejemplo.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+57 300 123 4567'}),
            'company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Empresa'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        
        # Validar no vacío
        if not name:
            raise ValidationError("El nombre del cliente es obligatorio.")
        
        # Validar longitud mínima
        if len(name) < 3:
            raise ValidationError("El nombre debe tener al menos 3 caracteres.")
        
        # Validar longitud máxima
        if len(name) > 100:
            raise ValidationError("El nombre no puede exceder 100 caracteres.")
        
        # Validar que no sea solo números
        if name.isdigit():
            raise ValidationError("El nombre no puede ser solo números.")
        
        return name.strip()
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        
        if not email:
            raise ValidationError("El email es obligatorio.")
        
        # Validar formato de email
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            raise ValidationError("El formato del email no es válido.")
        
        # Validar email único (excepto en edición del mismo cliente)
        existing = Customer.objects.filter(email=email).exclude(pk=self.instance.pk)
        if existing.exists():
            raise ValidationError(f"Este email ya está registrado en el cliente: {existing.first().name}")
        
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        
        if phone:
            # Validar formato básico (solo números, +, -, espacios)
            if not re.match(r'^[\d\s\+\-\(\)]{7,}$', phone):
                raise ValidationError("El formato del teléfono no es válido. Usa: +57 300 123 4567")
        
        return phone
    
    def clean_company(self):
        company = self.cleaned_data.get('company', '').strip()
        
        if company and len(company) > 100:
            raise ValidationError("El nombre de la empresa no puede exceder 100 caracteres.")
        
        return company
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validación cruzada: si está activo, debe tener email
        if cleaned_data.get('is_active') and not cleaned_data.get('email'):
            raise ValidationError("Un cliente activo debe tener un email registrado.")
        
        return cleaned_data


class AdvancedCustomerSearchForm(forms.Form):
    """Formulario avanzado de búsqueda de clientes"""
    
    SEARCH_BY_CHOICES = [
        ('', 'Buscar por...'),
        ('name', 'Nombre'),
        ('email', 'Email'),
        ('id', 'ID'),
        ('company', 'Empresa'),
    ]
    
    STATUS_CHOICES = [
        ('', 'Todos los estados'),
        (True, 'Activos'),
        (False, 'Inactivos'),
    ]
    
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Escribe nombre, email, ID o empresa...',
            'id': 'search-query'
        }),
        label='Búsqueda'
    )
    
    search_by = forms.ChoiceField(
        required=False,
        choices=SEARCH_BY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Tipo de búsqueda'
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Estado'
    )
    
    assigned_to = forms.ModelChoiceField(
        required=False,
        queryset=User.objects.filter(profile__role='vendedor'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Asignado a',
        empty_label='Todos los vendedores'
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Fecha desde'
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Fecha hasta'
    )
    
    order_by = forms.ChoiceField(
        required=False,
        choices=[
            ('-created_at', 'Más recientes'),
            ('created_at', 'Más antiguos'),
            ('name', 'Por nombre A-Z'),
            ('-name', 'Por nombre Z-A'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Ordenar por'
    )
