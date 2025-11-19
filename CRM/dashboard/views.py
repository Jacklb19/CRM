from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.contrib.auth.models import User
from customers.models import Customer
from opportunities.models import Opportunity  
from followups.models import Followup
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
        my_customers = Customer.objects.all()  # Cambiar a: .filter(assigned_to=user)
        my_opportunities = Opportunity.objects.filter(assigned_to=user)
        
        context.update({
            'total_customers': my_customers.count(),
            'active_customers': my_customers.filter(is_active=True).count(),
            'inactive_customers': my_customers.filter(is_active=False).count(),
            'my_opportunities': my_opportunities.count(),
            'opportunities_open': my_opportunities.filter(status='abierta').count(),
            'opportunities_won': my_opportunities.filter(status='ganada').count(),
            'opportunities_lost': my_opportunities.filter(status='perdida').count(),
        })
    
    elif role == 'gerente':
        all_customers = Customer.objects.all()
        all_opportunities = Opportunity.objects.all()
        
        # Rendimiento por vendedor
        salesrep_stats = Opportunity.objects.filter(
            status='ganada',
            assigned_to__profile__role='vendedor'
        ).values(
            'assigned_to__username'
        ).annotate(
            won_count=Count('id')
        ).order_by('-won_count')[:5]
        
        salesrep_names = [stat['assigned_to__username'] for stat in salesrep_stats]
        salesrep_won = [stat['won_count'] for stat in salesrep_stats]
        
        # Oportunidades por mes (últimos 6 meses)
        six_months_ago = datetime.now() - timedelta(days=180)
        opportunities_by_month = Opportunity.objects.filter(
            created_at__gte=six_months_ago
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        months_labels = [opp['month'].strftime('%b %Y') for opp in opportunities_by_month]
        opportunities_counts = [opp['count'] for opp in opportunities_by_month]
        
        context.update({
            'total_customers': all_customers.count(),
            'active_customers': all_customers.filter(is_active=True).count(),
            'inactive_customers': all_customers.filter(is_active=False).count(),
            'total_salespeople': User.objects.filter(profile__role='vendedor').count(),
            'total_opportunities': all_opportunities.count(),
            'opportunities_open': all_opportunities.filter(status='abierta').count(),
            'opportunities_won': all_opportunities.filter(status='ganada').count(),
            'opportunities_lost': all_opportunities.filter(status='perdida').count(),
            'salesrep_names': json.dumps(salesrep_names),
            'salesrep_won': json.dumps(salesrep_won),
            'months_labels': json.dumps(months_labels),
            'opportunities_by_month': json.dumps(opportunities_counts),
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
        
        context.update({
            'total_customers': all_customers.count(),
            'active_customers': all_customers.filter(is_active=True).count(),
            'inactive_customers': all_customers.filter(is_active=False).count(),
            'total_users': all_users.count(),
            'total_admins': all_users.filter(profile__role='administrador').count(),
            'total_managers': all_users.filter(profile__role='gerente').count(),
            'total_salespeople': all_users.filter(profile__role='vendedor').count(),
            'total_opportunities': all_opportunities.count(),
            'opportunities_open': all_opportunities.filter(status='abierta').count(),
            'opportunities_won': all_opportunities.filter(status='ganada').count(),
            'opportunities_lost': all_opportunities.filter(status='perdida').count(),
            'total_followups': all_followups.count(),
            'followup_types': json.dumps(followup_types),
            'followup_counts': json.dumps(followup_counts),
        })
    
    return render(request, 'dashboard/dashboard.html', context)
