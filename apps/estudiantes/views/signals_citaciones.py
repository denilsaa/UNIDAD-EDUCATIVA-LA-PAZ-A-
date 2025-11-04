from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.apps import apps as django_apps

from apps.citaciones.models.citacion import Citacion
from apps.citaciones.services.queue_service import sugerir_slot_por_mm1
from apps.citaciones.ws import push_propuesta_director  # helper pequeño (ver C)

KardexRegistro = django_apps.get_model("estudiantes", "KardexRegistro")
KardexItem = django_apps.get_model("estudiantes", "KardexItem")

def _cumple_regla(item: KardexItem, estudiante, ahora):
    """
    Política estricta:
    - directa = 1 ⇒ dispara
    - directa = 0 y umbral >= 1 ⇒ contar ocurrencias en ventana (≤ 15)
    - umbral = 0 y directa = 0 ⇒ NO dispara
    """
    if item.directa:
        return True, "Directa"

    umbral = int(item.umbral or 0)
    if umbral <= 0:
        return False, "No dispara (umbral=0 y directa=0)"

    ventana = min(int(item.ventana_dias or 0), 15) or 1
    desde = ahora - timezone.timedelta(days=ventana)

    Registro = KardexRegistro
    # contar mismo KardexItem del estudiante en la ventana
    cnt = (Registro.objects
           .filter(estudiante=estudiante, creado_en__gte=desde)
           .filter(kardex_item_id=item.id)
           .count())

    return (cnt + 1) >= umbral, f"Acumulación: {cnt+1}/{umbral} en {ventana} días"

@receiver(post_save, sender=KardexRegistro)
def proponer_citacion(sender, instance: KardexRegistro, created, **kwargs):
    if not created:
        return

    est = instance.estudiante
    item = instance.kardex_item
    ahora = timezone.now()

    dispara, razon = _cumple_regla(item, est, ahora)
    if not dispara:
        return

    # Citación en estado ABIERTA (pendiente de aprobación)
    cit = Citacion.objects.create(
        estudiante=est,
        kardex_registro=instance,
        motivo_resumen=getattr(item, "descripcion", "Citación"),
        estado=Citacion.Estado.ABIERTA,
        # sin fecha/hora todavía (solo sugerencia)
    )

    # ETA sugerida (informativa)
    ests, dt_sugerido = sugerir_slot_por_mm1(base_dt=ahora)

    # WS al Director (bandeja de aprobación)
    payload = {
        "citacion_id": cit.id,
        "estudiante": str(est),
        "motivo": cit.motivo_resumen,
        "razon": razon,
        "rho": ests["rho"],
        "Wq": ests["Wq"],
        "sugerido": dt_sugerido.isoformat(),
    }
    push_propuesta_director(payload)
