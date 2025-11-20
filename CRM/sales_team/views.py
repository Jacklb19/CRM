import logging
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum, Count
from django.utils import timezone
from .models import TeamMember
from opportunities.models import Opportunity
from followups.models import Followup

logger = logging.getLogger(__name__)


class ManagerRequiredMixin(LoginRequiredMixin):
    """Mixin para verificar que el usuario sea gerente o administrador"""
    def dispatch(self, request, *args, **kwargs):
        role = getattr(request.user.profile, 'role', None)
        if role not in ['gerente', 'administrador']:
            raise PermissionDenied("Solo gerentes y administradores pueden acceder a esta sección.")
        return super().dispatch(request, *args, **kwargs)


class SalesTeamListView(ManagerRequiredMixin, ListView):
    """Lista de todos los vendedores con métricas"""
    model = TeamMember
    template_name = 'sales_team/team_list.html'
    context_object_name = 'team_members'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = TeamMember.objects.filter(is_active_seller=True).select_related('user')
        
        # Filtro por búsqueda
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__username__icontains=search)
            )
        
        # Ordenar por opción
        sort_by = self.request.GET.get('sort_by', '-user__opportunities__amount')
        if sort_by == 'won_value':
            # Ordenar por valor ganado
            queryset = queryset.annotate(
                won_total=Sum('user__opportunities__amount', 
                             filter=Q(user__opportunities__status='ganada'))
            ).order_by('-won_total')
        elif sort_by == 'win_rate':
            # Esto es más complejo, mejor hacerlo en Python
            pass
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Métricas globales del equipo
        team_members = TeamMember.objects.filter(is_active_seller=True)
        
        context['total_sellers'] = team_members.count()
        context['total_opportunities'] = Opportunity.objects.filter(
            assigned_to__team_member__is_active_seller=True
        ).count()
        context['total_pipeline'] = Opportunity.objects.filter(
            assigned_to__team_member__is_active_seller=True,
            status__in=['abierta', 'calificada', 'propuesta', 'negociacion']
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_won'] = Opportunity.objects.filter(
            assigned_to__team_member__is_active_seller=True,
            status='ganada'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_followers'] = Followup.objects.filter(
            user__team_member__is_active_seller=True
        ).count()
        
        return context


class SalesTeamDetailView(ManagerRequiredMixin, DetailView):
    """Detalle de un vendedor individual"""
    model = TeamMember
    template_name = 'sales_team/team_detail.html'
    context_object_name = 'member'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member = self.get_object()
        
        # Oportunidades
        context['opportunities'] = Opportunity.objects.filter(assigned_to=member.user).order_by('-created_at')
        context['open_opportunities'] = context['opportunities'].filter(
            status__in=['abierta', 'calificada', 'propuesta', 'negociacion']
        )
        context['won_opportunities'] = context['opportunities'].filter(status='ganada')
        context['lost_opportunities'] = context['opportunities'].filter(status='perdida')
        
        # Seguimientos
        context['followups'] = Followup.objects.filter(user=member.user).order_by('-date')[:10]
        context['pending_followups'] = context['followups'].filter(status='pendiente')
        
        # Clientes
        context['customers'] = member.user.customers.all()
        
        # Métricas detalladas
        context['metrics'] = {
            'total_opportunities': member.get_total_opportunities(),
            'open_opportunities': member.get_open_opportunities(),
            'won_opportunities': member.get_won_opportunities(),
            'lost_opportunities': member.get_lost_opportunities(),
            'pipeline_value': member.get_total_pipeline_value(),
            'won_value': member.get_won_value(),
            'average_deal_size': member.get_average_deal_size(),
            'win_rate': member.get_win_rate(),
            'followups_count': member.get_followups_count(),
            'customers_count': member.get_total_customers(),
        }
        
        return context
