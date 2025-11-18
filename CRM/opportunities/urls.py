from django.urls import path
from .views import OpportunityCreateView, OpportunityListView, OpportunityDetailView

app_name = "opportunities"

urlpatterns = [
    path("", OpportunityListView.as_view(), name="list"),
    path("<int:pk>/", OpportunityDetailView.as_view(), name="detail"),
    path("nueva/", OpportunityCreateView.as_view(), name="create"),
]