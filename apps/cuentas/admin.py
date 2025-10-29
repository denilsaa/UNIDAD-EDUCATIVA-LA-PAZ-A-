# apps/cuentas/admin.py
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.contrib.auth import get_user_model

try:
    from .models import Rol
except Exception:
    Rol = None

Usuario = get_user_model()

# Campos disponibles en tu modelo Usuario
MODEL_FIELDS = {f.name for f in Usuario._meta.get_fields()}

def _has(field):  # helper
    return field in MODEL_FIELDS

# ---------- ROL ----------
if Rol:
    @admin.register(Rol)
    class RolAdmin(admin.ModelAdmin):
        list_display = ("nombre",)
        search_fields = ("nombre",)
        ordering = ("nombre",)

# ---------- USUARIO ----------
@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    """
    Admin robusto que no asume 'username'.
    Muestra un identificador inteligente y maneja ValidationError de señales.
    """

    # Identificador amigable (usa lo que exista)
    def identificador(self, obj):
        for attr in ("username", "email", "ci", "nombre", "first_name"):
            val = getattr(obj, attr, None)
            if val:
                return val
        return f"Usuario #{obj.pk}"
    identificador.short_description = "Usuario"

    def get_rol(self, obj):
        rol = getattr(obj, "rol", None)
        return getattr(rol, "nombre", "—")
    get_rol.short_description = "Rol"
    get_rol.admin_order_field = "rol__nombre"

    # Columnas de la lista
    list_display = ("identificador", "get_rol") + (("is_activo",) if _has("is_activo") else ())

    # Filtros
    list_filter = (("is_activo",) if _has("is_activo") else ()) + (("rol__nombre",) if _has("rol") else ())

    # Búsqueda (solo los que existan)
    _search_candidates = ("username", "email", "ci", "nombre", "first_name", "last_name")
    search_fields = tuple(f for f in _search_candidates if _has(f))

    # Orden por defecto seguro
    ordering = ("id",)

    # Campos del formulario (ajusta si tienes más)
    base_fields = []
    for f in ("username", "email", "ci", "nombre", "first_name", "last_name"):
        if _has(f):
            base_fields.append(f)
    if _has("rol"):
        base_fields.append("rol")
    if _has("is_activo"):
        base_fields.append("is_activo")
    fields = tuple(base_fields) if base_fields else ("id",)

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)
        except ValidationError as e:
            messages.error(request, getattr(e, "message", str(e)))
            raise

    @transaction.atomic
    def delete_model(self, request, obj):
        try:
            super().delete_model(request, obj)
        except ValidationError as e:
            messages.error(request, getattr(e, "message", str(e)))
            raise

    @transaction.atomic
    def delete_queryset(self, request, queryset):
        try:
            super().delete_queryset(request, queryset)
        except ValidationError as e:
            messages.error(request, getattr(e, "message", str(e)))
            raise
