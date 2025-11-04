# apps/citaciones/signals.py
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from apps.citaciones.models import Citacion
from apps.citaciones.services.notificaciones_service import notificar_citacion_aprobada

def _padres_ids(estudiante_id: int):
    # TODO: Ajusta según tus relaciones reales Estudiante -> Padres/Tutor.
    # Por ahora usa tutor_id si existe.
    from apps.estudiantes.models.estudiante import Estudiante
    e = Estudiante.objects.filter(pk=estudiante_id).only("tutor_id").first()
    return [e.tutor_id] if getattr(e, "tutor_id", None) else []

@receiver(pre_save, sender=Citacion)
def _guardar_estado_prev(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._estado_prev = sender.objects.only("estado").get(pk=instance.pk).estado
        except sender.DoesNotExist:
            instance._estado_prev = None
    else:
        instance._estado_prev = None

@receiver(post_save, sender=Citacion)
def _on_aprobada(sender, instance: Citacion, created, **kwargs):
    if getattr(instance, "_estado_prev", None) != "APROBADA" and instance.estado == "APROBADA":
        for uid in _padres_ids(instance.estudiante_id):
            if uid:
                notificar_citacion_aprobada(instance, uid)
