import logging
from django import forms
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models import Q, Sum, Count
from .models import Opportunity
from .forms import OpportunityForm, AdvancedOpportunitySearchForm
from customers.models import Customer


logger = logging.getLogger(__name__)


class VendedorRequiredMixin:
    """Mixin para verificar que el usuario sea vendedor, gerente o administrador"""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied
        
        role = getattr(request.user.profile, 'role', None)
        if role not in ['vendedor', 'gerente', 'administrador']:
            raise PermissionDenied
        
        return super().dispatch(request, *args, **kwargs)


class OpportunityListView(VendedorRequiredMixin, ListView):
    model = Opportunity
    template_name = 'opportunities/opportunity_list.html'
    context_object_name = 'opportunities'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = Opportunity.objects.all()
        
        # Vendedores solo ven sus oportunidades
        if self.request.user.profile.role == 'vendedor':
            queryset = queryset.filter(assigned_to=self.request.user)
        
        # BÚSQUEDA AVANZADA
        search_query = self.request.GET.get('search_query', '').strip()
        status_filter = self.request.GET.getlist('status')
        priority_filter = self.request.GET.getlist('priority')
        customer_filter = self.request.GET.get('customer', '')
        assigned_to_filter = self.request.GET.get('assigned_to', '')
        amount_from = self.request.GET.get('amount_from', '')
        amount_to = self.request.GET.get('amount_to', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        
        # Búsqueda por texto
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(customer__name__icontains=search_query) |
                Q(id__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Filtro de estado
        if status_filter:
            queryset = queryset.filter(status__in=status_filter)
        
        # Filtro de prioridad
        if priority_filter:
            queryset = queryset.filter(priority__in=priority_filter)
        
        # Filtro de cliente
        if customer_filter:
            queryset = queryset.filter(customer_id=customer_filter)
        
        # Filtro de vendedor (solo gerentes/admins)
        if assigned_to_filter and self.request.user.profile.role != 'vendedor':
            queryset = queryset.filter(assigned_to_id=assigned_to_filter)
        
        # Filtro de monto
        if amount_from:
            try:
                queryset = queryset.filter(amount__gte=float(amount_from))
            except ValueError:
                pass
        
        if amount_to:
            try:
                queryset = queryset.filter(amount__lte=float(amount_to))
            except ValueError:
                pass
        
        # Filtro de fecha
        if date_from:
            queryset = queryset.filter(expected_close_date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(expected_close_date__lte=date_to)
        
        # Ordenamiento
        order_by = self.request.GET.get('order_by', '-created_at')
        if order_by:
            queryset = queryset.order_by(order_by)
        
        return queryset.select_related('customer', 'assigned_to')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = AdvancedOpportunitySearchForm(self.request.GET or None)
        
        # Estadísticas
        user = self.request.user
        if user.profile.role == 'vendedor':
            user_opps = Opportunity.objects.filter(assigned_to=user)
        else:
            user_opps = Opportunity.objects.all()
        
        context['total_opportunities'] = user_opps.count()
        context['total_pipeline'] = user_opps.filter(
            status__in=['abierta', 'calificada', 'propuesta', 'negociacion']
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        context['won_opportunities'] = user_opps.filter(status='ganada').count()
        context['lost_opportunities'] = user_opps.filter(status='perdida').count()
        
        return context


class OpportunityDetailView(VendedorRequiredMixin, DetailView):
    model = Opportunity
    template_name = 'opportunities/opportunity_detail.html'
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if request.user.profile.role == 'vendedor' and obj.assigned_to != request.user:
            raise PermissionDenied("No tienes permiso para ver esta oportunidad.")
        return super().dispatch(request, *args, **kwargs)


class OpportunityCreateView(VendedorRequiredMixin, CreateView):
    model = Opportunity
    form_class = OpportunityForm
    template_name = 'opportunities/opportunity_form.html'
    success_url = reverse_lazy('opportunity_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.user.profile.role == 'vendedor':
            if 'assigned_to' in form.fields:
                form.fields['assigned_to'].widget = forms.HiddenInput()
        return form
    
    def form_valid(self, form):
        if self.request.user.profile.role == 'vendedor':
            form.instance.assigned_to = self.request.user
        logger.info(f"Nueva oportunidad creada por {self.request.user}: {form.instance.title}")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        logger.warning(f"Formulario inválido para usuario {self.request.user}: {form.errors}")
        return super().form_invalid(form)


class OpportunityUpdateView(VendedorRequiredMixin, UpdateView):
    model = Opportunity
    form_class = OpportunityForm
    template_name = 'opportunities/opportunity_form.html'
    success_url = reverse_lazy('opportunity_list')
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if request.user.profile.role == 'vendedor' and obj.assigned_to != request.user:
            raise PermissionDenied("No tienes permiso para editar esta oportunidad.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.user.profile.role == 'vendedor':
            if 'assigned_to' in form.fields:
                form.fields['assigned_to'].widget = forms.HiddenInput()
        return form
    
    def form_valid(self, form):
        if self.request.user.profile.role == 'vendedor':
            form.instance.assigned_to = self.request.user
        logger.info(f"Oportunidad actualizada por {self.request.user}: {form.instance.title}")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        logger.warning(f"Formulario inválido para usuario {self.request.user}: {form.errors}")
        return super().form_invalid(form)


class OpportunityDeleteView(VendedorRequiredMixin, DeleteView):
    model = Opportunity
    template_name = 'opportunities/opportunity_confirm_delete.html'
    success_url = reverse_lazy('opportunity_list')
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if request.user.profile.role == 'vendedor' and obj.assigned_to != request.user:
            raise PermissionDenied("No tienes permiso para eliminar esta oportunidad.")
        return super().dispatch(request, *args, **kwargs)
