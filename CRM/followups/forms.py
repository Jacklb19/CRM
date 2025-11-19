from django import forms
from .models import Followup

class FollowupForm(forms.ModelForm):
    class Meta:
        model = Followup
        fields = ['customer', 'opportunity', 'type', 'subject', 'notes', 'date']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'opportunity': forms.Select(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Asunto del seguimiento'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Notas del seguimiento'}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
