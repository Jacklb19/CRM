from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

from .models import FollowUp
from customers.models import Customer
from opportunities.models import Opportunity
from .forms import FollowUpForm


# --- Decorador para roles ---
def role_required(*roles):
    def decorator(view_func):
        def _wrapped(request, *args, **kwargs):
            if request.user.profile.role not in roles:
                messages.error(request, "No tienes permisos para acceder.")
                return redirect("dashboard:index")
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


# ============================
#  LISTADO GENERAL
# ============================
@method_decorator(login_required, name="dispatch")
class FollowUpListView(ListView):
    model = FollowUp
    template_name = "followups/followup_list.html"
    context_object_name = "followups"

    def get_queryset(self):
        role = self.request.user.profile.role

        # Admin → ve todo
        if role == "admin":
            return FollowUp.objects.select_related(
                "related_customer",
                "related_opportunity",
                "created_by"
    )

        # Vendedor → solo sus followups
        if role == "vendedor":
            return FollowUp.objects.filter(created_by=self.request.user)

        # Cliente → solo followups asociados a él
        if role == "cliente":
            customer = Customer.objects.filter(user=self.request.user).first()
            if customer:
                return FollowUp.objects.filter(customer=customer)
            return FollowUp.objects.none()

        return FollowUp.objects.none()


# ============================
#  CREAR
# ============================
@method_decorator(login_required, name="dispatch")
@method_decorator(role_required("admin", "vendedor"), name="dispatch")
class FollowUpCreateView(CreateView):
    model = FollowUp
    form_class = FollowUpForm
    template_name = "followups/followup_form.html"
    success_url = reverse_lazy("followups:list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Seguimiento registrado exitosamente.")
        return super().form_valid(form)


# ============================
#  EDITAR
# ============================
@method_decorator(login_required, name="dispatch")
@method_decorator(role_required("admin", "vendedor"), name="dispatch")
class FollowUpUpdateView(UpdateView):
    model = FollowUp
    form_class = FollowUpForm
    template_name = "followups/followup_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Seguimiento actualizado.")
        return super().form_valid(form)


# ============================
#  ELIMINAR
# ============================
@method_decorator(login_required, name="dispatch")
@method_decorator(role_required("admin", "vendedor"), name="dispatch")
class FollowUpDeleteView(DeleteView):
    model = FollowUp
    template_name = "followups/followup_confirm_delete.html"
    success_url = reverse_lazy("followups:list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Seguimiento eliminado.")
        return super().delete(request, *args, **kwargs)
