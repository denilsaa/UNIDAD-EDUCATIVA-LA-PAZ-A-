from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from apps.estudiantes.models import Estudiante
from .models import StudentLog
from .utils import get_request, get_ip_ua_from_request


# ---------- Helpers internos ----------

def _repr_estudiante(est: Estudiante | None) -> str:
    if not est:
        return ""
    partes = [f"{est.apellidos}, {est.nombres}"]
    if getattr(est, "ci", None):
        partes.append(f"CI: {est.ci}")
    if getattr(est, "curso", None):
        partes.append(f"Curso: {est.curso}")
    return " | ".join(partes)


def _valor_campo(est: Estudiante | None, field: str) -> str:
    if not est:
        return "—"

    val = getattr(est, field, None)

    if field in ("curso", "padre"):
        return str(val) if val else "—"

    if field == "fecha_nac":
        return est.fecha_nac.strftime("%d/%m/%Y") if est.fecha_nac else "—"

    if field == "sexo":
        return est.get_sexo_display() if getattr(est, "sexo", None) else "—"

    return val or "—"


CAMPOS_DETALLE = [
    ("ci", "CI"),
    ("nombres", "Nombres"),
    ("apellidos", "Apellidos"),
    ("fecha_nac", "Fecha de nacimiento"),
    ("sexo", "Sexo"),
    ("curso", "Curso"),
    ("padre", "Padre de familia"),
]


# ---------- Guardar estado anterior antes de modificar ----------

@receiver(pre_save, sender=Estudiante)
def cache_original_estudiante(sender, instance, **kwargs):
    """
    Antes de guardar, si ya existe en BD, guardamos una copia
    del estado anterior para comparar luego en post_save.
    """
    if not instance.pk:
        return
    try:
        original = Estudiante.objects.get(pk=instance.pk)
    except Estudiante.DoesNotExist:
        original = None
    instance._original_estudiante = original


# ---------- post_save: creación / modificación ----------

@receiver(post_save, sender=Estudiante)
def log_estudiante_save(sender, instance, created, **kwargs):
    """
    Registra creación y modificación de estudiantes.
    """
    request = get_request()
    ip, ua = get_ip_ua_from_request(request)
    user = getattr(request, "user", None) if request else None
    if user is not None and not getattr(user, "is_authenticated", False):
        user = None

    est_repr = _repr_estudiante(instance)

    if created:
        # Descripción detallada de creación
        detalles = []
        for field, label in CAMPOS_DETALLE:
            detalles.append(f"{label}: {_valor_campo(instance, field)}")
        desc = (
            f"Creó el estudiante {est_repr}. "
            f"Datos registrados -> " + "; ".join(detalles) + "."
        )
        accion = StudentLog.Accion.CREAR
    else:
        # Descripción de modificación, comparando valores
        original = getattr(instance, "_original_estudiante", None)
        cambios = []

        if original:
            for field, label in CAMPOS_DETALLE:
                antes = _valor_campo(original, field)
                despues = _valor_campo(instance, field)
                if antes != despues:
                    cambios.append(f"{label}: '{antes}' → '{despues}'")
        else:
            # Por si no tenemos original, al menos registramos el estado actual
            for field, label in CAMPOS_DETALLE:
                cambios.append(f"{label}: {_valor_campo(instance, field)}")

        if cambios:
            desc = (
                f"Modificó datos del estudiante {est_repr}. "
                f"Cambios -> " + "; ".join(cambios) + "."
            )
        else:
            desc = (
                f"Modificó al estudiante {est_repr}, "
                f"pero no se detectaron cambios en los campos principales."
            )

        accion = StudentLog.Accion.EDITAR

    StudentLog.objects.create(
        usuario=user,
        estudiante=instance,
        estudiante_nombre=est_repr,
        accion=accion,
        descripcion=desc,
        ip=ip,
        user_agent=ua,
    )


# ---------- post_delete: eliminación ----------

@receiver(post_delete, sender=Estudiante)
def log_estudiante_delete(sender, instance, **kwargs):
    """
    Registra eliminación de estudiantes.
    """
    request = get_request()
    ip, ua = get_ip_ua_from_request(request)
    user = getattr(request, "user", None) if request else None
    if user is not None and not getattr(user, "is_authenticated", False):
        user = None

    est_repr = _repr_estudiante(instance)

    detalles = []
    for field, label in CAMPOS_DETALLE:
        detalles.append(f"{label}: {_valor_campo(instance, field)}")

    desc = (
        f"Eliminó al estudiante {est_repr}. "
        f"Últimos datos registrados -> " + "; ".join(detalles) + "."
    )

    StudentLog.objects.create(
        usuario=user,
        estudiante=None,           # ya no existe en BD
        estudiante_nombre=est_repr,  # pero guardamos el nombre/CI/curso
        accion=StudentLog.Accion.ELIMINAR,
        descripcion=desc,
        ip=ip,
        user_agent=ua,
    )
