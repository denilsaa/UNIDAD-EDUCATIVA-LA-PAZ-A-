from django.contrib import admin
from .models.asistencia_config import AsistenciaCalendario, AsistenciaExclusion

@admin.register(AsistenciaCalendario)
class AsistenciaCalendarioAdmin(admin.ModelAdmin):
    list_display = ("fecha_inicio","fecha_fin","lunes","martes","miercoles","jueves","viernes","activo")
    list_filter = ("activo",)
    search_fields = ("fecha_inicio","fecha_fin")

@admin.register(AsistenciaExclusion)
class AsistenciaExclusionAdmin(admin.ModelAdmin):
    list_display = ("calendario","fecha")
    list_filter = ("calendario",)
