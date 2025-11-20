from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Count
from django.utils import timezone
from .models import Customer
from .forms import AdvancedCustomerSearchForm
from .mixins import VendedorRequiredMixin


# ================================================================
# LISTA DE CLIENTES
# ================================================================

class CustomerListView(VendedorRequiredMixin, ListView):
    model = Customer
    template_name = 'customers/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filtrado por rol
        if user.profile.role == 'vendedor':
            queryset = queryset.filter(assigned_to=user)
        
        # BÚSQUEDA AVANZADA
        form = AdvancedCustomerSearchForm(self.request.GET or None)
        
        search_query = self.request.GET.get('search_query', '').strip()
        search_by = self.request.GET.get('search_by', '')
        status = self.request.GET.get('status', '')
        assigned_to = self.request.GET.get('assigned_to', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        
        # Búsqueda por tipo específico
        if search_query:
            if search_by == 'name':
                queryset = queryset.filter(name__icontains=search_query)
            elif search_by == 'email':
                queryset = queryset.filter(email__icontains=search_query)
            elif search_by == 'id':
                try:
                    customer_id = int(search_query)
                    queryset = queryset.filter(id=customer_id)
                except ValueError:
                    queryset = queryset.none()
            elif search_by == 'company':
                queryset = queryset.filter(company__icontains=search_query)
            else:
                # Búsqueda global en todos los campos
                queryset = queryset.filter(
                    Q(name__icontains=search_query) |
                    Q(email__icontains=search_query) |
                    Q(company__icontains=search_query) |
                    Q(id__icontains=search_query)
                )
        
        # Filtro de estado
        if status == 'True':
            queryset = queryset.filter(is_active=True)
        elif status == 'False':
            queryset = queryset.filter(is_active=False)
        
        # Filtro de vendedor
        if assigned_to and user.profile.role != 'vendedor':
            queryset = queryset.filter(assigned_to_id=assigned_to)
        
        # Filtro de fecha
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        # Ordenamiento
        order_by = self.request.GET.get('order_by', '-created_at')
        if order_by:
            queryset = queryset.order_by(order_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = AdvancedCustomerSearchForm(self.request.GET or None)
        
        # Estadísticas
        user = self.request.user
        if user.profile.role == 'vendedor':
            user_customers = Customer.objects.filter(assigned_to=user)
        else:
            user_customers = Customer.objects.all()
        
        context['total_customers'] = user_customers.count()
        context['active_customers'] = user_customers.filter(is_active=True).count()
        context['inactive_customers'] = user_customers.filter(is_active=False).count()
        
        return context


# ================================================================
# DETALLE DE CLIENTE ⭐ CORREGIDO ⭐
# ================================================================

class CustomerDetailView(VendedorRequiredMixin, DetailView):
    model = Customer
    template_name = 'customers/customer_detail.html'
    context_object_name = 'customer'  # ⭐ AGREGADO
    
    def dispatch(self, request, *args, **kwargs):
        """Verificar permisos de acceso"""
        obj = self.get_object()
        if request.user.profile.role == 'vendedor' and obj.assigned_to != request.user:
            raise PermissionDenied("No tienes permiso para ver este cliente.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """⭐ PROCESAR DATOS PARA EVITAR FILTRO SPLIT ⭐"""
        context = super().get_context_data(**kwargs)
        customer = self.object
        
        # Calcular días desde creación (evita usar split en template)
        if customer.created_at:
            delta = timezone.now() - customer.created_at
            context['days_since_created'] = delta.days
        else:
            context['days_since_created'] = 0
        
        # Obtener estadísticas del cliente
        context['total_opportunities'] = customer.opportunities.count()
        context['active_opportunities'] = customer.opportunities.filter(
            status__in=['abierta', 'calificada', 'propuesta', 'negociacion']
        ).count()
        context['won_opportunities'] = customer.opportunities.filter(status='ganada').count()
        context['lost_opportunities'] = customer.opportunities.filter(status='perdida').count()
        
        # Calcular valor total de oportunidades
        from django.db.models import Sum
        total_pipeline = customer.opportunities.filter(
            status__in=['abierta', 'calificada', 'propuesta', 'negociacion']
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        total_won = customer.opportunities.filter(
            status='ganada'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        context['total_pipeline'] = total_pipeline
        context['total_won'] = total_won
        
        return context


# ================================================================
# CREAR CLIENTE
# ================================================================

class CustomerCreateView(VendedorRequiredMixin, CreateView):
    model = Customer
    fields = ['name', 'email', 'phone', 'company', 'is_active']
    template_name = 'customers/customer_form.html'
    success_url = reverse_lazy('customer_list')
    
    def form_valid(self, form):
        # Asignar automáticamente al vendedor si es vendedor
        if self.request.user.profile.role == 'vendedor':
            form.instance.assigned_to = self.request.user
        return super().form_valid(form)


# ================================================================
# ACTUALIZAR CLIENTE
# ================================================================

class CustomerUpdateView(VendedorRequiredMixin, UpdateView):
    model = Customer
    fields = ['name', 'email', 'phone', 'company', 'is_active']
    template_name = 'customers/customer_form.html'
    success_url = reverse_lazy('customer_list')
    context_object_name = 'customer'  # ⭐ AGREGADO
    
    def dispatch(self, request, *args, **kwargs):
        """Verificar permisos de edición"""
        obj = self.get_object()
        if request.user.profile.role == 'vendedor' and obj.assigned_to != request.user:
            raise PermissionDenied("No tienes permiso para editar este cliente.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.profile.role == 'vendedor':
            queryset = queryset.filter(assigned_to=user)
        return queryset


# ================================================================
# ELIMINAR CLIENTE
# ================================================================

class CustomerDeleteView(VendedorRequiredMixin, DeleteView):
    model = Customer
    template_name = 'customers/customer_confirm_delete.html'
    success_url = reverse_lazy('customer_list')
    context_object_name = 'customer'  # ⭐ AGREGADO
    
    def dispatch(self, request, *args, **kwargs):
        """Verificar permisos de eliminación"""
        obj = self.get_object()
        if request.user.profile.role == 'vendedor' and obj.assigned_to != request.user:
            raise PermissionDenied("No tienes permiso para eliminar este cliente.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.profile.role == 'vendedor':
            queryset = queryset.filter(assigned_to=user)
        return queryset
