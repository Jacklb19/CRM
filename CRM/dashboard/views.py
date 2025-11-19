from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.contrib.auth.models import User
from customers.models import Customer
# from opportunities.models import Opportunity  # cuando lo implementes
# from followups.models import Followup

@login_required
def dashboard_view(request):
    user = request.user
    role = user.profile.role
    
    context = {
        'role': role,
        'user': user,
    }
    
    # ===== VENDEDOR: Solo ve sus propios datos =====
    if role == 'vendedor':
        # Clientes asignados al vendedor (cuando agregues campo 'assigned_to' en Customer)
        # Por ahora mostramos todos, pero deberías filtrar por vendedor
        my_customers = Customer.objects.all()  # Cambiar a: .filter(assigned_to=user)
        
        context.update({
            'total_customers': my_customers.count(),
            'active_customers': my_customers.filter(is_active=True).count(),
            'inactive_customers': my_customers.filter(is_active=False).count(),
            # Cuando implementes opportunities:
            # 'my_opportunities': Opportunity.objects.filter(assigned_to=user).count(),
            # 'opportunities_open': Opportunity.objects.filter(assigned_to=user, status='abierta').count(),
            # 'opportunities_won': Opportunity.objects.filter(assigned_to=user, status='ganada').count(),
        })
    
    # ===== GERENTE: Ve datos de todo su equipo =====
    elif role == 'gerente':
        # Total de clientes del sistema (o de su equipo si tienes jerarquía)
        all_customers = Customer.objects.all()
        
        # Vendedores activos en el sistema
        total_salespeople = User.objects.filter(profile__role='vendedor').count()
        
        context.update({
            'total_customers': all_customers.count(),
            'active_customers': all_customers.filter(is_active=True).count(),
            'inactive_customers': all_customers.filter(is_active=False).count(),
            'total_salespeople': total_salespeople,
            # Cuando implementes opportunities:
            # 'total_opportunities': Opportunity.objects.count(),
            # 'opportunities_open': Opportunity.objects.filter(status='abierta').count(),
            # 'opportunities_won': Opportunity.objects.filter(status='ganada').count(),
            # 'opportunities_lost': Opportunity.objects.filter(status='perdida').count(),
        })
    
    # ===== ADMINISTRADOR: Ve todo el sistema =====
    elif role == 'administrador':
        all_customers = Customer.objects.all()
        all_users = User.objects.filter(profile__isnull=False)
        
        context.update({
            'total_customers': all_customers.count(),
            'active_customers': all_customers.filter(is_active=True).count(),
            'inactive_customers': all_customers.filter(is_active=False).count(),
            'total_users': all_users.count(),
            'total_admins': all_users.filter(profile__role='administrador').count(),
            'total_managers': all_users.filter(profile__role='gerente').count(),
            'total_salespeople': all_users.filter(profile__role='vendedor').count(),
            # Cuando implementes opportunities y followups:
            # 'total_opportunities': Opportunity.objects.count(),
            # 'total_followups': Followup.objects.count(),
        })
    
    return render(request, 'dashboard/dashboard.html', context)
