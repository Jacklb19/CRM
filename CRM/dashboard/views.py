from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.contrib.auth.models import User
from customers.models import Customer
from opportunities.models import Opportunity  
from followups.models import Followup
from sales_team.models import TeamMember
from datetime import datetime, timedelta
from django.db.models.functions import TruncMonth
import json


@login_required
def dashboard_view(request):
    user = request.user
    role = user.profile.role
    
    context = {
        'role': role,
        'user': user,
    }
    
    if role == 'vendedor':
        # Clientes del vendedor
        my_customers = Customer.objects.filter(assigned_to=user)
        my_opportunities = Opportunity.objects.filter(assigned_to=user)
        my_followups = Followup.objects.filter(user=user)
        
        # Datos para gráficos
        opportunities_by_status = my_opportunities.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        status_map = {
            'abierta': 'Abierta',
            'calificada': 'Calificada',
            'propuesta': 'Propuesta',
            'negociacion': 'Negociación',
            'ganada': 'Ganada',
            'perdida': 'Perdida',
        }
        
        status_labels = [status_map.get(stat['status'], stat['status']) for stat in opportunities_by_status]
        status_data = [stat['count'] for stat in opportunities_by_status]
        
        # Oportunidades por prioridad
        opportunities_by_priority = my_opportunities.values('priority').annotate(
            count=Count('id')
        )
        
        priority_map = {
            'alta': 'Alta',
            'media': 'Media',
            'baja': 'Baja',
        }
        
        priority_labels = [priority_map.get(prior['priority'], prior['priority']) for prior in opportunities_by_priority]
        priority_data = [prior['count'] for prior in opportunities_by_priority]
        
        context.update({
            'total_customers': my_customers.count(),
            'active_customers': my_customers.filter(is_active=True).count(),
            'inactive_customers': my_customers.filter(is_active=False).count(),
            'my_opportunities': my_opportunities.count(),
            'opportunities_open': my_opportunities.filter(status__in=['abierta', 'calificada', 'propuesta', 'negociacion']).count(),
            'opportunities_won': my_opportunities.filter(status='ganada').count(),
            'opportunities_lost': my_opportunities.filter(status='perdida').count(),
            'total_pipeline_value': my_opportunities.filter(status__in=['abierta', 'calificada', 'propuesta', 'negociacion']).aggregate(Sum('amount'))['amount__sum'] or 0,
            'total_won_value': my_opportunities.filter(status='ganada').aggregate(Sum('amount'))['amount__sum'] or 0,
            'pending_followups': my_followups.filter(status='pendiente').count(),
            'status_labels': json.dumps(status_labels),
            'status_data': json.dumps(status_data),
            'priority_labels': json.dumps(priority_labels),
            'priority_data': json.dumps(priority_data),
        })
    
    elif role == 'gerente':
        all_customers = Customer.objects.all()
        all_opportunities = Opportunity.objects.all()
        all_users = User.objects.filter(profile__role='vendedor')
        
        # Rendimiento por vendedor
        salesrep_stats = []
        for seller in all_users:
            team_member = TeamMember.objects.filter(user=seller).first()
            if team_member:
                salesrep_stats.append({
                    'username': seller.username,
                    'won_count': team_member.get_won_opportunities(),
                    'pipeline_value': team_member.get_total_pipeline_value(),
                })
        
        salesrep_stats_sorted = sorted(salesrep_stats, key=lambda x: x['won_count'], reverse=True)[:5]
        salesrep_names = [stat['username'] for stat in salesrep_stats_sorted]
        salesrep_won = [stat['won_count'] for stat in salesrep_stats_sorted]
        
        # Oportunidades por estado
        opportunities_by_status = all_opportunities.values('status').annotate(
            count=Count('id')
        )
        
        status_map = {
            'abierta': 'Abierta',
            'calificada': 'Calificada',
            'propuesta': 'Propuesta',
            'negociacion': 'Negociación',
            'ganada': 'Ganada',
            'perdida': 'Perdida',
        }
        
        status_labels = [status_map.get(stat['status'], stat['status']) for stat in opportunities_by_status]
        status_data = [stat['count'] for stat in opportunities_by_status]
        
        # Oportunidades por mes (últimos 12 meses)
        twelve_months_ago = datetime.now() - timedelta(days=365)
        opportunities_by_month = all_opportunities.filter(
            created_at__gte=twelve_months_ago
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id'),
            total_value=Sum('amount')
        ).order_by('month')
        
        months_labels = [opp['month'].strftime('%b %Y') if opp['month'] else '' for opp in opportunities_by_month]
        opportunities_counts = [opp['count'] for opp in opportunities_by_month]
        opportunities_values = [float(opp['total_value'] or 0) for opp in opportunities_by_month]
        
        # Total pipeline
        total_pipeline = all_opportunities.filter(
            status__in=['abierta', 'calificada', 'propuesta', 'negociacion']
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        context.update({
            'total_customers': all_customers.count(),
            'active_customers': all_customers.filter(is_active=True).count(),
            'inactive_customers': all_customers.filter(is_active=False).count(),
            'total_salespeople': all_users.count(),
            'total_opportunities': all_opportunities.count(),
            'opportunities_open': all_opportunities.filter(status__in=['abierta', 'calificada', 'propuesta', 'negociacion']).count(),
            'opportunities_won': all_opportunities.filter(status='ganada').count(),
            'opportunities_lost': all_opportunities.filter(status='perdida').count(),
            'total_pipeline_value': total_pipeline,
            'salesrep_names': json.dumps(salesrep_names),
            'salesrep_won': json.dumps(salesrep_won),
            'months_labels': json.dumps(months_labels),
            'opportunities_by_month': json.dumps(opportunities_counts),
            'opportunities_values_by_month': json.dumps(opportunities_values),
            'status_labels': json.dumps(status_labels),
            'status_data': json.dumps(status_data),
        })
    
    elif role == 'administrador':
        all_customers = Customer.objects.all()
        all_users = User.objects.filter(profile__isnull=False)
        all_opportunities = Opportunity.objects.all()
        all_followups = Followup.objects.all()
        
        # Seguimientos por tipo
        followup_stats = all_followups.values('type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        followup_type_map = {
            'llamada': 'Llamada',
            'email': 'Email',
            'reunion': 'Reunión',
            'nota': 'Nota'
        }
        
        followup_types = [followup_type_map.get(stat['type'], stat['type']) for stat in followup_stats]
        followup_counts = [stat['count'] for stat in followup_stats]
        
        # Oportunidades por estado
        opportunities_by_status = all_opportunities.values('status').annotate(
            count=Count('id')
        )
        
        status_map = {
            'abierta': 'Abierta',
            'calificada': 'Calificada',
            'propuesta': 'Propuesta',
            'negociacion': 'Negociación',
            'ganada': 'Ganada',
            'perdida': 'Perdida',
        }
        
        status_labels = [status_map.get(stat['status'], stat['status']) for stat in opportunities_by_status]
        status_data = [stat['count'] for stat in opportunities_by_status]
        
        context.update({
            'total_customers': all_customers.count(),
            'active_customers': all_customers.filter(is_active=True).count(),
            'inactive_customers': all_customers.filter(is_active=False).count(),
            'total_users': all_users.count(),
            'total_admins': all_users.filter(profile__role='administrador').count(),
            'total_managers': all_users.filter(profile__role='gerente').count(),
            'total_salespeople': all_users.filter(profile__role='vendedor').count(),
            'total_opportunities': all_opportunities.count(),
            'opportunities_open': all_opportunities.filter(status__in=['abierta', 'calificada', 'propuesta', 'negociacion']).count(),
            'opportunities_won': all_opportunities.filter(status='ganada').count(),
            'opportunities_lost': all_opportunities.filter(status='perdida').count(),
            'total_followups': all_followups.count(),
            'followup_types': json.dumps(followup_types),
            'followup_counts': json.dumps(followup_counts),
            'status_labels': json.dumps(status_labels),
            'status_data': json.dumps(status_data),
        })
    
    return render(request, 'dashboard/dashboard.html', context)
