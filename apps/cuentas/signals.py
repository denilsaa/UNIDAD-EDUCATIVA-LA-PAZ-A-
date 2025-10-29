from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from apps.cuentas.roles import es_director

Usuario = get_user_model()

def _count_directores_activos(exclude_pk=None) -> int:
    qs = Usuario.objects.filter(is_activo=True)
    # usa tu helper para filtrar en Python (suficiente y claro)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    # filtra sólo los que sean director (según tu lógica actual)
    return sum(1 for u in qs.select_related("rol") if es_director(u))

@receiver(pre_save, sender=Usuario)
def evitar_quedarse_sin_director_al_guardar(sender, instance: Usuario, **kwargs):
    """
    Bloquea:
      - cambiar el rol del ÚLTIMO Director a otro rol
      - desactivar (is_activo=False) al ÚLTIMO Director
    """
    if not instance.pk:
        # Creación: no reduce el conteo de directores
        return

    actual = Usuario.objects.select_related("rol").get(pk=instance.pk)

    actual_es_dir = es_director(actual)
    nuevo_es_dir  = es_director(instance)

    actual_activo = bool(getattr(actual, "is_activo", True))
    nuevo_activo  = bool(getattr(instance, "is_activo", True))

    # pierde el rol de director
    pierde_rol_director = actual_es_dir and not nuevo_es_dir
    # se desactiva un director
    se_desactiva_director = actual_es_dir and actual_activo and not nuevo_activo

    if pierde_rol_director or se_desactiva_director:
        restantes = _count_directores_activos(exclude_pk=instance.pk)
        if restantes == 0:
            raise ValidationError("Operación bloqueada: debe existir al menos un Director activo en el sistema.")

@receiver(pre_delete, sender=Usuario)
def evitar_quedarse_sin_director_al_eliminar(sender, instance: Usuario, **kwargs):
    """
    Bloquea eliminar al último Director activo.
    """
    if es_director(instance) and bool(getattr(instance, "is_activo", True)):
        restantes = _count_directores_activos(exclude_pk=instance.pk)
        if restantes == 0:
            raise ValidationError("No puedes eliminar al último Director activo.")
