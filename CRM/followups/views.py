from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied

from .models import FollowUp
from .forms import FollowUpForm


# ============================
#  MIXIN PROFESIONAL DE ROLES
# ============================
class CommercialAccessMixin:
    """Permite acceso solo a administrador, gerente y vendedor."""
    allowed_roles = ["administrador", "gerente", "vendedor"]

    def dispatch(self, request, *args, **kwargs):
        if request.user.profile.role not in self.allowed_roles:
            messages.error(request, "No tienes permisos para acceder a esta sección.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


# ============================
#  LISTADO
# ============================
@method_decorator(login_required, name="dispatch")
class FollowUpListView(CommercialAccessMixin, ListView):
    model = FollowUp
    template_name = "followups/followup_list.html"
    context_object_name = "followups"

    def get_queryset(self):
        role = self.request.user.profile.role

        # ADMIN + GERENTE → ven todo
        if role in ["administrador", "gerente"]:
            return FollowUp.objects.select_related(
                "related_customer",
                "related_opportunity",
                "created_by"
            )

        # VENDEDOR → solo sus followups
        if role == "vendedor":
            return FollowUp.objects.filter(created_by=self.request.user)

        return FollowUp.objects.none()


# ============================
#  CREAR
# ============================
@method_decorator(login_required, name="dispatch")
class FollowUpCreateView(CommercialAccessMixin, CreateView):
    model = FollowUp
    form_class = FollowUpForm
    template_name = "followups/followup_form.html"
    success_url = reverse_lazy("followups:list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Seguimiento creado correctamente.")
        return super().form_valid(form)


# ============================
#  EDITAR
# ============================
@method_decorator(login_required, name="dispatch")
class FollowUpUpdateView(CommercialAccessMixin, UpdateView):
    model = FollowUp
    form_class = FollowUpForm
    template_name = "followups/followup_form.html"
    success_url = reverse_lazy("followups:list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Seguimiento actualizado.")
        return super().form_valid(form)


# ============================
#  ELIMINAR
# ============================
@method_decorator(login_required, name="dispatch")
class FollowUpDeleteView(CommercialAccessMixin, DeleteView):
    model = FollowUp
    template_name = "followups/followup_confirm_delete.html"
    success_url = reverse_lazy("followups:list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Seguimiento eliminado.")
        return super().delete(request, *args, **kwargs)
