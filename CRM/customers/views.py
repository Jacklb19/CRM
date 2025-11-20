from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.db.models import Q

from .models import Customer


# ===========================
#      MIXIN DE ROLES
# ===========================
class RoleRequiredMixin(LoginRequiredMixin):
    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if request.user.profile.role not in self.allowed_roles:
            messages.error(request, "No tienes permisos para acceder a esta sección.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


# ===========================
#      LISTADO DE CLIENTES
# ===========================
class CustomerListView(RoleRequiredMixin, ListView):
    model = Customer
    template_name = 'customers/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 10
    allowed_roles = ("administrador", "vendedor", "gerente")

    def get_queryset(self):
        qs = Customer.objects.all()
        role = self.request.user.profile.role

        # Vendedor → solo sus clientes
        if role == "vendedor":
            qs = qs.filter(owner=self.request.user)

        # Buscador
        search = self.request.GET.get("search")
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(company__icontains=search)
            )
        return qs


# ===========================
#      DETALLE
# ===========================
class CustomerDetailView(RoleRequiredMixin, DetailView):
    model = Customer
    template_name = 'customers/customer_detail.html'
    allowed_roles = ("administrador", "vendedor", "gerente")

    # Bloqueo vendedor accediendo a cliente ajeno
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if request.user.profile.role == "vendedor" and obj.owner != request.user:
            messages.warning(request, "No puedes ver clientes de otro vendedor.")
            return redirect("customer_list")
        return super().dispatch(request, *args, **kwargs)


# ===========================
#      CREAR CLIENTE
# ===========================
class CustomerCreateView(RoleRequiredMixin, CreateView):
    model = Customer
    fields = ['name', 'email', 'phone', 'company', 'is_active']
    template_name = 'customers/customer_form.html'
    success_url = reverse_lazy('customer_list')
    allowed_roles = ("administrador", "vendedor", "gerente")

    def form_valid(self, form):
        form.instance.owner = self.request.user  # Asignar dueño automáticamente
        messages.success(self.request, "Cliente creado exitosamente.")
        return super().form_valid(form)


# ===========================
#      EDITAR CLIENTE
# ===========================
class CustomerUpdateView(RoleRequiredMixin, UpdateView):
    model = Customer
    fields = ['name', 'email', 'phone', 'company', 'is_active']
    template_name = 'customers/customer_form.html'
    success_url = reverse_lazy('customer_list')
    allowed_roles = ("administrador", "vendedor", "gerente")

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()

        if request.user.profile.role == "vendedor" and obj.owner != request.user:
            messages.error(request, "No puedes editar un cliente que no es tuyo.")
            return redirect("customer_list")

        return super().dispatch(request, *args, **kwargs)


# ===========================
#      ELIMINAR CLIENTE
# ===========================
class CustomerDeleteView(RoleRequiredMixin, DeleteView):
    model = Customer
    template_name = 'customers/customer_confirm_delete.html'
    success_url = reverse_lazy('customer_list')
    allowed_roles = ("administrador", "vendedor", "gerente")

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()

        if request.user.profile.role == "vendedor" and obj.owner != request.user:
            messages.error(request, "No puedes eliminar un cliente que no es tuyo.")
            return redirect("customer_list")

        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Cliente eliminado correctamente.")
        return super().delete(request, *args, **kwargs)
