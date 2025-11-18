from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView

from .models import Opportunity
from .forms import OpportunityForm

class OpportunityListView(LoginRequiredMixin, ListView):
    model = Opportunity
    template_name = "opportunities/opportunity_list.html"
    context_object_name = "opportunities"

class OpportunityDetailView(LoginRequiredMixin, DetailView):
    model = Opportunity
    template_name = "opportunities/opportunity_detail.html"
    context_object_name = "opportunity"

class OpportunityCreateView(LoginRequiredMixin, CreateView):
    model = Opportunity
    form_class = OpportunityForm
    template_name = "opportunities/opportunity_form.html"
    success_url = reverse_lazy("opportunities:list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)
