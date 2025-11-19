from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from .models import Followup
from .forms import FollowupForm

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
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(subject__icontains=search)
        
        return queryset

class FollowupDetailView(VendedorRequiredMixin, DetailView):
    model = Followup
    template_name = 'followups/followup_detail.html'

class FollowupCreateView(VendedorRequiredMixin, CreateView):
    model = Followup
    form_class = FollowupForm
    template_name = 'followups/followup_form.html'
    success_url = reverse_lazy('followup_list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class FollowupUpdateView(VendedorRequiredMixin, UpdateView):
    model = Followup
    form_class = FollowupForm
    template_name = 'followups/followup_form.html'
    success_url = reverse_lazy('followup_list')

class FollowupDeleteView(VendedorRequiredMixin, DeleteView):
    model = Followup
    template_name = 'followups/followup_confirm_delete.html'
    success_url = reverse_lazy('followup_list')
