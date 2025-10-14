from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum, Max
from .citacion_motivo import CitacionMotivo
from .citacion import Citacion

def _recalcular(citacion_id: int):
    agg = CitacionMotivo.objects.filter(citacion_id=citacion_id).aggregate(
        total=Sum("motivo__peso_prioridad_default"),
        maxsev=Max("motivo__severidad_default"),
    )
    Citacion.objects.filter(id=citacion_id).update(
        puntaje_motivos=agg["total"] or 0,
        severidad=agg["maxsev"] or 1
    )

@receiver(post_save, sender=CitacionMotivo)
def cm_creado(sender, instance, created, **kwargs):
    if created:
        _recalcular(instance.citacion_id)

@receiver(post_delete, sender=CitacionMotivo)
def cm_borrado(sender, instance, **kwargs):
    _recalcular(instance.citacion_id)
