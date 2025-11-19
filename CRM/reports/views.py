from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .forms import ReportFilterForm
from customers.models import Customer
from opportunities.models import Opportunity
from followups.models import Followup

@login_required
def report_view(request):
    if request.user.profile.role not in ('administrador', 'gerente'):
        raise PermissionDenied("No tienes permiso para acceder a esta sección")

    form = ReportFilterForm(request.GET or None)
    report_data = None

    if form.is_valid():
        data = form.cleaned_data
        # Ejemplo: filtrar oportunidades
        opportunities = Opportunity.objects.all()
        if data.get('start_date'):
            opportunities = opportunities.filter(created_at__gte=data['start_date'])
        if data.get('end_date'):
            opportunities = opportunities.filter(created_at__lte=data['end_date'])
        if data.get('customer'):
            opportunities = opportunities.filter(customer=data['customer'])
        if data.get('assigned_to'):
            opportunities = opportunities.filter(assigned_to=data['assigned_to'])
        
        # Similar para clientes o seguimientos si quieres incluir
        
        report_data = opportunities  # Aquí podrías combinar varios queryset o procesar datos

    context = {
        'form': form,
        'report_data': report_data,
    }
    return render(request, 'reports/report.html', context)
