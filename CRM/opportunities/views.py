import logging
from django import forms
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from .models import Opportunity
from .forms import OpportunityForm

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
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Vendedores solo ven sus oportunidades
        if self.request.user.profile.role == 'vendedor':
            queryset = queryset.filter(assigned_to=self.request.user)
        
        # Filtros opcionales
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search) | queryset.filter(customer__name__icontains=search)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Contar oportunidades vencidas y próximas a vencer
        if self.request.user.profile.role == 'vendedor':
            context['overdue_count'] = Opportunity.objects.filter(
                assigned_to=self.request.user,
                status__in=['abierta', 'calificada', 'propuesta', 'negociacion'],
                expected_close_date__lt=timezone.now().date()
            ).count()
            
            context['due_soon_count'] = Opportunity.objects.filter(
                assigned_to=self.request.user,
                status__in=['abierta', 'calificada', 'propuesta', 'negociacion'],
                expected_close_date__gte=timezone.now().date(),
                expected_close_date__lte=timezone.now().date() + timezone.timedelta(days=7)
            ).count()
            
            context['total_value'] = sum(
                opp.amount for opp in Opportunity.objects.filter(
                    assigned_to=self.request.user,
                    status__in=['abierta', 'calificada', 'propuesta', 'negociacion']
                )
            )
        
        return context


class OpportunityDetailView(VendedorRequiredMixin, DetailView):
    model = Opportunity
    template_name = 'opportunities/opportunity_detail.html'
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        # Vendedores solo pueden ver sus propias oportunidades
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
