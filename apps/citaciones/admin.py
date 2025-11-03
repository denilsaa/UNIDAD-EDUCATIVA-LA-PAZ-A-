# apps/citaciones/admin.py
from django.contrib import admin
from .models import Citacion

@admin.register(Citacion)
class CitacionAdmin(admin.ModelAdmin):
    list_display = ("id", "estudiante", "estado", "fecha_citacion", "hora_citacion", "motivo_resumen")
    list_filter = ("estado",)
    search_fields = ("estudiante__nombres", "estudiante__apellidos", "motivo_resumen")
