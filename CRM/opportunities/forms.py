from django import forms
from .models import Opportunity

class OpportunityForm(forms.ModelForm):
    class Meta:
        model = Opportunity
        fields = [
            "title",
            "customer",
            "amount",
            "expected_close_date",
            "probability",
            "status",
            "description",
        ]
        widgets = {
            "expected_close_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }
