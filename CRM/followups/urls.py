from django.urls import path
from .views import (
    FollowUpListView,
    FollowUpCreateView,
    FollowUpUpdateView,
    FollowUpDeleteView,
)

app_name = "followups"

urlpatterns = [
    # LISTADO
    path("", FollowUpListView.as_view(), name="list"),

    # CREAR
    path("nuevo/", FollowUpCreateView.as_view(), name="create"),

    # EDITAR
    path("<int:pk>/editar/", FollowUpUpdateView.as_view(), name="edit"),

    # ELIMINAR
    path("<int:pk>/eliminar/", FollowUpDeleteView.as_view(), name="delete"),
]
