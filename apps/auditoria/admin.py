from django.contrib import admin
from .models import StudentLog


@admin.register(StudentLog)
class StudentLogAdmin(admin.ModelAdmin):
  list_display = ("creado_en", "usuario", "accion", "estudiante", "ip")
  list_filter = ("accion", "creado_en")
  search_fields = (
    "usuario__username",
    "usuario__nombre",
    "estudiante__nombres",
    "estudiante__apellidos",
    "descripcion",
    "ip",
  )
