import logging
from django.views.generic import ListView, DetailView
from django.db.models import Q, Count, Sum, Avg
from django.core.exceptions import PermissionDenied
from .models import TeamMember
from opportunities.models import Opportunity
from followups.models import Followup


logger = logging.getLogger(__name__)


class ManagerRequiredMixin:
    """Mixin para verificar que el usuario sea gerente o administrador"""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied
        
        role = getattr(request.user.profile, 'role', None)
        if role not in ['gerente', 'administrador']:
            raise PermissionDenied("Solo gerentes y administradores pueden acceder aquí")
        
        return super().dispatch(request, *args, **kwargs)


class SalesTeamListView(ManagerRequiredMixin, ListView):
    """Lista de todos los vendedores con búsqueda mejorada"""
    model = TeamMember
    template_name = 'sales_team/team_list.html'
    context_object_name = 'team_members'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = TeamMember.objects.filter(is_active_seller=True).select_related('user')
        
        # BÚSQUEDA MEJORADA
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__username__icontains=search) |
                Q(department__icontains=search)
            )
        
        # ORDENAMIENTO - Con filtros de oportunidades y ganancias
        order_by = self.request.GET.get('order_by', '-user__date_joined')
        
        if order_by == 'won_value':
            queryset = queryset.annotate(
                won_total=Sum('user__opportunities__amount', 
                            filter=Q(user__opportunities__status='ganada'))
            ).order_by('-won_total')
        elif order_by == 'opportunities':
            queryset = queryset.annotate(
                opp_count=Count('user__opportunities')
            ).order_by('-opp_count')
        elif order_by == 'customers':
            queryset = queryset.annotate(
                cust_count=Count('user__customers')
            ).order_by('-cust_count')
        elif order_by == 'pipeline':
            queryset = queryset.annotate(
                pipeline_total=Sum('user__opportunities__amount',
                                filter=Q(user__opportunities__status__in=['abierta', 'calificada', 'propuesta', 'negociacion']))
            ).order_by('-pipeline_total')
        elif order_by:
            queryset = queryset.order_by(order_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Enriquecer datos para cada miembro
        team_data = []
        for member in self.object_list:
            opps = member.user.opportunities.all()
            won = opps.filter(status='ganada')
            team_data.append({
                'member': member,
                'customers_count': member.user.customers.count(),
                'opportunities_count': opps.count(),
                'won_count': won.count(),
                'pipeline': opps.filter(status__in=['abierta', 'calificada', 'propuesta', 'negociacion']).aggregate(Sum('amount'))['amount__sum'] or 0,
            })
        
        context['team_data'] = team_data
        
        # Métricas globales
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
        opportunities = Opportunity.objects.filter(assigned_to=member.user).order_by('-created_at')
        context['opportunities'] = opportunities
        context['open_opportunities'] = opportunities.filter(status__in=['abierta', 'calificada', 'propuesta', 'negociacion'])
        context['won_opportunities'] = opportunities.filter(status='ganada')
        context['lost_opportunities'] = opportunities.filter(status='perdida')
        
        # Seguimientos
        followups = Followup.objects.filter(user=member.user).order_by('-date')
        context['followups'] = followups[:10]
        context['pending_followups'] = followups.filter(status='pendiente')
        
        # Clientes
        context['customers'] = member.user.customers.all()
        
        # Métricas
        context['metrics'] = {
            'total_opportunities': opportunities.count(),
            'open_opportunities': context['open_opportunities'].count(),
            'won_opportunities': context['won_opportunities'].count(),
            'lost_opportunities': context['lost_opportunities'].count(),
            'pipeline_value': context['open_opportunities'].aggregate(Sum('amount'))['amount__sum'] or 0,
            'won_value': context['won_opportunities'].aggregate(Sum('amount'))['amount__sum'] or 0,
            'average_deal_size': opportunities.aggregate(Avg('amount'))['amount__avg'] or 0,
            'win_rate': (context['won_opportunities'].count() / opportunities.count() * 100) if opportunities.count() > 0 else 0,
            'followups_count': Followup.objects.filter(user=member.user).count(),
            'customers_count': member.user.customers.count(),
        }
        
        return context
