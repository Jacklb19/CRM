import logging
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from .models import Followup
from .forms import FollowupForm, AdvancedFollowupSearchForm  
from django.db.models import Q


logger = logging.getLogger(__name__)


class VendedorRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied
        
        role = getattr(request.user.profile, 'role', None)
        if role not in ['vendedor', 'gerente', 'administrador']:
            raise PermissionDenied
        
        return super().dispatch(request, *args, **kwargs)


class FollowupListView(VendedorRequiredMixin, ListView):
    model = Followup
    template_name = 'followups/followup_list.html'
    context_object_name = 'followups'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Vendedores solo ven sus seguimientos
        if self.request.user.profile.role == 'vendedor':
            queryset = queryset.filter(user=self.request.user)
        
        # Filtros opcionales
        type_filter = self.request.GET.get('type')
        if type_filter:
            queryset = queryset.filter(type=type_filter)
        
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(subject__icontains=search)
        
        return queryset.order_by('-date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Contar seguimientos vencidos y próximos para notificación
        if self.request.user.profile.role == 'vendedor':
            context['overdue_count'] = Followup.objects.filter(
                user=self.request.user,
                status='pendiente',
                date__lt=timezone.now()
            ).count()
            
            context['due_soon_count'] = Followup.objects.filter(
                user=self.request.user,
                status='pendiente',
                date__gte=timezone.now(),
                date__lte=timezone.now() + timezone.timedelta(hours=24)
            ).count()
        
        return context


class FollowupDetailView(VendedorRequiredMixin, DetailView):
    model = Followup
    template_name = 'followups/followup_detail.html'
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        # Vendedores solo pueden ver sus propios seguimientos
        if request.user.profile.role == 'vendedor' and obj.user != request.user:
            raise PermissionDenied("No tienes permiso para ver este seguimiento.")
        return super().dispatch(request, *args, **kwargs)


class FollowupCreateView(VendedorRequiredMixin, CreateView):
    model = Followup
    form_class = FollowupForm
    template_name = 'followups/followup_form.html'
    success_url = reverse_lazy('followup_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['is_create'] = True  # Flag para indicar que es creación
        return kwargs
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.status = 'pendiente'  # Asignar status automáticamente
        logger.info(f"Nuevo seguimiento creado por {self.request.user}: {form.instance.subject}")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        logger.warning(f"Formulario inválido para usuario {self.request.user}: {form.errors}")
        return super().form_invalid(form)


class FollowupUpdateView(VendedorRequiredMixin, UpdateView):
    model = Followup
    form_class = FollowupForm
    template_name = 'followups/followup_form.html'
    success_url = reverse_lazy('followup_list')
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        # Vendedores solo pueden editar sus propios seguimientos
        if request.user.profile.role == 'vendedor' and obj.user != request.user:
            raise PermissionDenied("No tienes permiso para editar este seguimiento.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['is_create'] = False  # Flag para indicar que es edición
        return kwargs
    
    def form_valid(self, form):
        logger.info(f"Seguimiento actualizado por {self.request.user}: {form.instance.subject}")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        logger.warning(f"Formulario inválido para usuario {self.request.user}: {form.errors}")
        return super().form_invalid(form)


class FollowupDeleteView(VendedorRequiredMixin, DeleteView):
    model = Followup
    template_name = 'followups/followup_confirm_delete.html'
    success_url = reverse_lazy('followup_list')
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        # Vendedores solo pueden eliminar sus propios seguimientos
        if request.user.profile.role == 'vendedor' and obj.user != request.user:
            raise PermissionDenied("No tienes permiso para eliminar este seguimiento.")
        return super().dispatch(request, *args, **kwargs)

class FollowupListView(VendedorRequiredMixin, ListView):
    model = Followup
    template_name = 'followups/followup_list.html'
    context_object_name = 'followups'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Vendedores solo ven sus seguimientos
        if self.request.user.profile.role == 'vendedor':
            queryset = queryset.filter(user=self.request.user)
        
        # BÚSQUEDA AVANZADA
        search_query = self.request.GET.get('search_query', '').strip()
        type_filter = self.request.GET.getlist('type')
        status_filter = self.request.GET.getlist('status')
        customer_filter = self.request.GET.get('customer', '')
        assigned_to_filter = self.request.GET.get('assigned_to', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        
        # Búsqueda por texto
        if search_query:
            queryset = queryset.filter(
                Q(subject__icontains=search_query) |
                Q(notes__icontains=search_query) |
                Q(customer__name__icontains=search_query)
            )
        
        # Filtro de tipo
        if type_filter:
            queryset = queryset.filter(type__in=type_filter)
        
        # Filtro de estado
        if status_filter:
            queryset = queryset.filter(status__in=status_filter)
        
        # Filtro de cliente
        if customer_filter:
            queryset = queryset.filter(customer_id=customer_filter)
        
        # Filtro de usuario (solo para gerentes/admins)
        if assigned_to_filter and self.request.user.profile.role != 'vendedor':
            queryset = queryset.filter(user_id=assigned_to_filter)
        
        # Filtro de fecha
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        # Ordenamiento
        order_by = self.request.GET.get('order_by', '-date')
        if order_by:
            queryset = queryset.order_by(order_by)
        
        return queryset.select_related('customer', 'user', 'opportunity')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = AdvancedFollowupSearchForm(self.request.GET or None)
        
        # Estadísticas
        user = self.request.user
        if user.profile.role == 'vendedor':
            user_followups = Followup.objects.filter(user=user)
        else:
            user_followups = Followup.objects.all()
        
        context['total_followups'] = user_followups.count()
        context['pending_followups'] = user_followups.filter(status='pendiente').count()
        context['completed_followups'] = user_followups.filter(status='completado').count()
        
        return context