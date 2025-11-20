from django.contrib import admin
from .models import Opportunity


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "customer",
        "owner",
        "status",
        "amount",
        "created_at",
    )

    list_display_links = ("title",)

    list_filter = (
        "status",
        "created_at",
        "owner",
    )

    search_fields = (
        "title",
        "customer__name",     # verifica que "name" existe en Customer
        "owner__username",
    )

    readonly_fields = ("created_at", "updated_at")

    ordering = ("-created_at",)

    list_per_page = 20

    fieldsets = (
        ("Información General", {
            "fields": ("title", "customer", "owner", "description")
        }),
        ("Datos Comerciales", {
            "fields": ("amount", "probability", "status", "expected_close_date")
        }),
        ("Tiempos", {
            "fields": ("created_at", "updated_at")
        }),
    )
