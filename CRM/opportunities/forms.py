from django import forms
from .models import Opportunity
from django.contrib.auth.models import User
from customers.models import Customer


class OpportunityForm(forms.ModelForm):
    class Meta:
        model = Opportunity
        fields = ['title', 'customer', 'assigned_to', 'status', 'amount', 'expected_close_date', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título de la oportunidad'}),
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'expected_close_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Descripción de la oportunidad'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and user.profile.role == 'vendedor':
            self.fields.pop('assigned_to')
            self.fields['customer'].queryset = Customer.objects.filter(assigned_to=user)
        else:
            self.fields['assigned_to'].queryset = User.objects.filter(profile__role='vendedor')
            self.fields['customer'].queryset = Customer.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        assigned_to = cleaned_data.get('assigned_to')
        customer = cleaned_data.get('customer')
        
        if assigned_to and customer:
            if customer.assigned_to != assigned_to:
                vendedor_real = customer.assigned_to.username if customer.assigned_to else "ninguno"
                raise forms.ValidationError(
                    f"Error: El cliente '{customer.name}' está asignado al vendedor '{vendedor_real}'. "
                    f"Por favor, asigna la oportunidad correctamente."
                )
        return cleaned_data
