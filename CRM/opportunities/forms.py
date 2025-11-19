from django import forms
from .models import Opportunity
from customers.models import Customer
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class OpportunityForm(forms.ModelForm):
    class Meta:
        model = Opportunity
        fields = ['title', 'customer', 'assigned_to', 'status', 'priority', 'amount', 'expected_close_date', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título de la oportunidad'}),
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'expected_close_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Descripción de la oportunidad'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar clientes según el rol del usuario
        if user and user.profile.role == 'vendedor':
            self.fields.pop('assigned_to', None)
            self.fields['customer'].queryset = Customer.objects.filter(assigned_to=user)
        else:
            self.fields['assigned_to'].queryset = User.objects.filter(profile__role='vendedor')
            self.fields['customer'].queryset = Customer.objects.all()
    
    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get('title')
        customer = cleaned_data.get('customer')
        assigned_to = cleaned_data.get('assigned_to')
        amount = cleaned_data.get('amount')
        expected_close_date = cleaned_data.get('expected_close_date')
        status = cleaned_data.get('status')
        
        # Validación 1: Título no vacío
        if title and len(title.strip()) < 5:
            raise forms.ValidationError(
                "El título debe tener al menos 5 caracteres."
            )
        
        # Validación 2: Monto positivo
        if amount is not None and amount <= 0:
            raise forms.ValidationError(
                "El monto estimado debe ser mayor que cero."
            )
        
        # Validación 3: Monto máximo razonable
        if amount is not None and amount > 999999999:
            raise forms.ValidationError(
                "El monto estimado no puede exceder 999,999,999."
            )
        
        # Vadiciones fecha
        if expected_close_date:
            today = timezone.now().date()
            
            if not self.instance.pk and expected_close_date < today:
                raise forms.ValidationError(
                    "La fecha estimada de cierre no puede ser en el pasado."
                )
            
            if (expected_close_date - today).days > 730:
                raise forms.ValidationError(
                    "La fecha estimada de cierre no puede ser más de 2 años en el futuro."
                )
            
            if (expected_close_date - today).days < 1:
                raise forms.ValidationError(
                    "La fecha estimada de cierre debe ser al menos mañana."
                )
        
        if assigned_to and customer:
            if customer.assigned_to != assigned_to:
                vendedor_real = customer.assigned_to.username if customer.assigned_to else "sin asignar"
                raise forms.ValidationError(
                    f"Error: El cliente '{customer.name}' está asignado al vendedor '{vendedor_real}'. "
                    f"No puedes asignar esta oportunidad a otro vendedor. "
                    f"Por favor, elige el vendedor correcto o un cliente diferente."
                )
        
        if customer and not customer.is_active:
            raise forms.ValidationError(
                f"Advertencia: El cliente '{customer.name}' está marcado como inactivo. "
                f"¿Estás seguro que deseas continuar?"
            )
        
        if status in ['ganada', 'perdida'] and not cleaned_data.get('description', '').strip():
            raise forms.ValidationError(
                f"Cuando marques la oportunidad como '{status}', debes incluir una descripción explicando el motivo."
            )
        
        return cleaned_data
