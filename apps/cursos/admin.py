from django.contrib import admin
from .models import Curso, Kardex

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ("id", "nivel", "paralelo", "regente", "creado_en")
    search_fields = ("nivel", "paralelo", "regente__username", "regente__first_name", "regente__last_name")
    list_filter = ("nivel",)
    ordering = ("nivel", "paralelo")

@admin.register(Kardex)
class KardexAdmin(admin.ModelAdmin):
    list_display = ("id", "curso", "anio", "trimestre", "creado_en")
    list_filter = ("anio", "trimestre")
    search_fields = ("curso__nivel", "curso__paralelo")
    ordering = ("-anio", "-trimestre")
