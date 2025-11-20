from django.urls import path
from .views import (
    OpportunityListView,
    OpportunityDetailView,
    OpportunityCreateView,
    OpportunityUpdateView,
    OpportunityDeleteView
)

app_name = "opportunities"

urlpatterns = [
    # Listado
    path("", OpportunityListView.as_view(), name="list"),

    # Crear oportunidad
    path("nueva/", OpportunityCreateView.as_view(), name="create"),

    # Detalle de oportunidad
    path("<int:pk>/", OpportunityDetailView.as_view(), name="detail"),

    # Editar oportunidad
    path("<int:pk>/editar/", OpportunityUpdateView.as_view(), name="update"),

    # Eliminar oportunidad
    path("<int:pk>/eliminar/", OpportunityDeleteView.as_view(), name="delete"),
]
