import logging
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from .models import Followup
from .forms import FollowupForm

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
