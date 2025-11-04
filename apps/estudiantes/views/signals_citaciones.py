from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now

from apps.estudiantes.models.kardex_registro import KardexRegistro
from apps.citaciones.models.citacion import Citacion

# (Opcional) notificación por WS; si no está, no romper
try:
    from apps.citaciones.ws import push_propuesta_director
except Exception:
    def push_propuesta_director(_):
        pass


@receiver(post_save, sender=KardexRegistro)
def generar_citacion_desde_kardex(sender, instance: KardexRegistro, created, **kwargs):
    if not created:
        return

    item = getattr(instance, "kardex_item", None)
    est = getattr(instance, "estudiante", None)
    if not item or not est or not getattr(item, "activo", True):
        return

    motivo_txt = (getattr(item, "descripcion", "") or "").strip() or "Motivo de citación"

    # 1) DIRECTA
    if getattr(item, "directa", 0):
        if Citacion.objects.filter(kardex_registro=instance).exists():
            return
        c = Citacion.objects.create(
            estudiante=est,
            kardex_registro=instance,
            motivo_resumen=motivo_txt[:160],
            estado=Citacion.Estado.ABIERTA,
            duracion_min=30,
        )
        try:
            push_propuesta_director({
                "citacion_id": c.id,
                "estudiante": str(est),
                "motivo": c.motivo_resumen,
                "razon": "Directa",
                "rho": None, "Wq": None, "sugerido": None,
            })
        except Exception:
            pass
        return

    # 2) ACUMULACIÓN
    umbral = int(getattr(item, "umbral", 0) or 0)
    ventana = int(getattr(item, "ventana_dias", 0) or 0)
    if umbral <= 0:
        return
    if ventana <= 0 or ventana > 15:
        ventana = 15

    desde = now().date() - timedelta(days=ventana)
    total = (KardexRegistro.objects
             .filter(estudiante=est, kardex_item=item, fecha__gte=desde)
             .count())
    if total < umbral:
        return

    ya_hay = (Citacion.objects
              .filter(estudiante=est,
                      estado__in=[Citacion.Estado.ABIERTA,
                                  Citacion.Estado.AGENDADA,
                                  Citacion.Estado.NOTIFICADA],
                      motivo_resumen__icontains=motivo_txt[:50],
                      creado_en__gte=now() - timedelta(days=ventana))
              .exists())
    if ya_hay:
        return

    c = Citacion.objects.create(
        estudiante=est,
        kardex_registro=instance,
        motivo_resumen=motivo_txt[:160],
        estado=Citacion.Estado.ABIERTA,
        duracion_min=30,
    )
    try:
        push_propuesta_director({
            "citacion_id": c.id,
            "estudiante": str(est),
            "motivo": c.motivo_resumen,
            "razon": f"Acumulación (≥{umbral} en {ventana} días)",
            "rho": None, "Wq": None, "sugerido": None,
        })
    except Exception:
        pass
