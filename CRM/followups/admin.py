from django.contrib import admin
from .models import FollowUp


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):

    list_display = (
        "followup_type",
        "related_customer",
        "related_opportunity",
        "created_by",
        "next_contact_date",
        "created_at",
    )

    list_filter = (
        "followup_type",
        "next_contact_date",
        "created_at",
    )

    search_fields = (
        "notes",
        "related_customer__name",
        "related_opportunity__title",
        "created_by__username",
    )

    readonly_fields = (
        "created_at",
        "created_by",
    )

    ordering = ("-created_at",)

    list_per_page = 20

    fieldsets = (
        ("Información del Seguimiento", {
            "fields": (
                "followup_type",
                "notes",
                "next_contact_date",
            )
        }),
        ("Relaciones", {
            "fields": (
                "related_customer",
                "related_opportunity",
            )
        }),
        ("Datos del Sistema", {
            "fields": (
                "created_by",
                "created_at",
            )
        }),
    )
