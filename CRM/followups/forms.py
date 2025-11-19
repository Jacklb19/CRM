from django import forms
from .models import Followup
from customers.models import Customer
from opportunities.models import Opportunity
from django.utils import timezone


class FollowupForm(forms.ModelForm):
    class Meta:
        model = Followup
        fields = ['customer', 'opportunity', 'type', 'subject', 'notes', 'date', 'status']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'opportunity': forms.Select(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Asunto del seguimiento'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Notas del seguimiento'}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        is_create = kwargs.pop('is_create', False)  # Flag para saber si es creación o edición
        super().__init__(*args, **kwargs)
        
        # Filtrar clientes según el rol del usuario
        if user and user.profile.role == 'vendedor':
            self.fields['customer'].queryset = Customer.objects.filter(assigned_to=user)
            self.fields['opportunity'].queryset = Opportunity.objects.filter(assigned_to=user)
        else:
            self.fields['customer'].queryset = Customer.objects.all()
            self.fields['opportunity'].queryset = Opportunity.objects.all()
        
        # En creación, ocultar el campo status (será "pendiente" automáticamente)
        if is_create:
            self.fields.pop('status', None)

    def clean(self):
        cleaned_data = super().clean()
        customer = cleaned_data.get('customer')
        opportunity = cleaned_data.get('opportunity')
        date = cleaned_data.get('date')
        
        # Validar que la oportunidad pertenezca al cliente
        if opportunity and customer:
            if opportunity.customer != customer:
                raise forms.ValidationError(
                    "La oportunidad seleccionada no pertenece al cliente elegido. "
                    f"El cliente de esa oportunidad es '{opportunity.customer.name}'."
                )
        
        # Validar que la fecha no sea en el pasado
        if date and date < timezone.now():
            raise forms.ValidationError("La fecha no puede ser en el pasado.")
        
        return cleaned_data
