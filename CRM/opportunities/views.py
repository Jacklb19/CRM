from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView,
    UpdateView, DeleteView
)

from .models import Opportunity
from .forms import OpportunityForm


# Mixin para permitir solo: admin, gerente, vendedor
class CommercialAccessMixin(UserPassesTestMixin):

    def test_func(self):
        return self.request.user.profile.role in ["administrador", "gerente", "vendedor"]

    def handle_no_permission(self):
        from django.shortcuts import redirect
        return redirect("dashboard")


class OpportunityListView(LoginRequiredMixin, CommercialAccessMixin, ListView):
    model = Opportunity
    template_name = "opportunities/opportunity_list.html"
    context_object_name = "opportunities"

    def get_queryset(self):
        user = self.request.user

        # Admin y gerente ven todas
        if user.profile.role in ["administrador", "gerente"]:
            return Opportunity.objects.all()

        # Vendedor solo ve las suyas
        return Opportunity.objects.filter(owner=user)


class OpportunityDetailView(LoginRequiredMixin, CommercialAccessMixin, DetailView):
    model = Opportunity
    template_name = "opportunities/opportunity_detail.html"
    context_object_name = "opportunity"


class OpportunityCreateView(LoginRequiredMixin, CommercialAccessMixin, CreateView):
    model = Opportunity
    form_class = OpportunityForm
    template_name = "opportunities/opportunity_form.html"
    success_url = reverse_lazy("opportunities:list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user  # enviar usuario al form
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class OpportunityUpdateView(LoginRequiredMixin, CommercialAccessMixin, UpdateView):
    model = Opportunity
    form_class = OpportunityForm
    template_name = "opportunities/opportunity_form.html"
    success_url = reverse_lazy("opportunities:list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class OpportunityDeleteView(LoginRequiredMixin, CommercialAccessMixin, DeleteView):
    model = Opportunity
    template_name = "opportunities/opportunity_confirm_delete.html"
    success_url = reverse_lazy("opportunities:list")
