from datetime import timedelta

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now

from apps.estudiantes.models.kardex_registro import KardexRegistro
from apps.citaciones.models.citacion import Citacion
from apps.citaciones.models.config import AtencionConfig

# (Opcional) notificación por WS; si no está, no romper
try:
    from apps.citaciones.ws import push_propuesta_director
except Exception:  # en tests/ambientes sin WS
    def push_propuesta_director(_payload):
        return


def _obtener_o_acumular_citacion(estudiante, kdx_registro, motivo_txt, duracion_base=30):
    """
    Si el estudiante YA tiene una citación (ABIERTA / AGENDADA / NOTIFICADA)
    para el MISMO DÍA del registro de kárdex:
        ➜ no crea nueva citación,
        ➜ solo aumenta la duración de la misma (+15 min)
        ➜ concatena el motivo.

    Si NO tiene citación ese día:
        ➜ crea una nueva con duración base (config).

    Esto mantiene la idea M/M/1: un solo cliente en la cola por día,
    pero con mayor tiempo de servicio cuando se acumulan faltas.
    """
    motivo_txt = (motivo_txt or "").strip()
    cfg = AtencionConfig.objects.first()
    dur_def = int(getattr(cfg, "duracion_por_defecto", duracion_base) or duracion_base)

    with transaction.atomic():
        existente = (
            Citacion.objects
            .select_for_update()
            .filter(
                estudiante=estudiante,
                estado__in=[
                    Citacion.Estado.ABIERTA,
                    Citacion.Estado.AGENDADA,
                    Citacion.Estado.NOTIFICADA,
                ],
                kardex_registro__fecha=kdx_registro.fecha,
            )
            .order_by("creado_en")
            .first()
        )

        if existente is not None:
            # incremento fijo de 15 min por nueva falta en el mismo día
            incremento = 15
            base = int(existente.duracion_min or dur_def)
            existente.duracion_min = base + incremento

            if motivo_txt:
                if existente.motivo_resumen:
                    if motivo_txt not in existente.motivo_resumen:
                        existente.motivo_resumen = (
                            f"{existente.motivo_resumen}; {motivo_txt}"
                        )[:160]
                else:
                    existente.motivo_resumen = motivo_txt[:160]

            existente.save(update_fields=["duracion_min", "motivo_resumen", "actualizado_en"])
            return existente, False

        # primera falta del día → duración base
        nueva = Citacion.objects.create(
            estudiante=estudiante,
            kardex_registro=kdx_registro,
            motivo_resumen=motivo_txt[:160] if motivo_txt else "",
            estado=Citacion.Estado.ABIERTA,
            duracion_min=dur_def,
        )
        return nueva, True


@receiver(post_save, sender=KardexRegistro)
def generar_citacion_desde_kardex(sender, instance: KardexRegistro, created, **kwargs):
    """
    Signal que se dispara cada vez que se crea un KardexRegistro.

    Aplica dos tipos de regla:

      1) Citación DIRECTA (campo `directa` del KardexItem)
      2) Citación por ACUMULACIÓN (campos `umbral` y `ventana_dias`)

    En ambos casos se respeta:
      ➜ si el estudiante ya tiene citación ABIERTA/AGENDADA/NOTIFICADA
         para el MISMO DÍA, se acumula tiempo y motivo en esa misma citación
         (no se crea una nueva).
    """
    if not created:
        return

    item = getattr(instance, "kardex_item", None)
    est = getattr(instance, "estudiante", None)
    if not item or not est or not getattr(item, "activo", True):
        return

    motivo_txt = (getattr(item, "descripcion", "") or "").strip() or "Motivo de citación"

    # 1) DIRECTA
    if getattr(item, "directa", 0):
        # Por seguridad: si este registro YA tiene citación vinculada, no duplicar
        if Citacion.objects.filter(kardex_registro=instance).exists():
            return

        c, creada = _obtener_o_acumular_citacion(
            estudiante=est,
            kdx_registro=instance,
            motivo_txt=motivo_txt,
            duracion_base=30,
        )
        try:
            razon = "Directa (nueva)" if creada else "Directa (acumulada)"
            push_propuesta_director({
                "citacion_id": c.id,
                "estudiante": str(est),
                "motivo": c.motivo_resumen,
                "razon": razon,
                "rho": None,
                "Wq": None,
                "sugerido": None,
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
    total = (
        KardexRegistro.objects
        .filter(
            estudiante=est,
            kardex_item=item,
            fecha__gte=desde,
        )
        .count()
    )
    if total < umbral:
        # Todavía no alcanza el umbral
        return

    # Aquí ya se cumple la regla de acumulación:
    # en lugar de crear SIEMPRE una nueva, acumulamos en la existente (si la hay).
    c, creada = _obtener_o_acumular_citacion(
        estudiante=est,
        kdx_registro=instance,
        motivo_txt=motivo_txt,
        duracion_base=30,
    )

    try:
        razon_base = f"Acumulación (≥{umbral} en {ventana} días"
        if creada:
            razon = f"{razon_base}, nueva)"
        else:
            razon = f"{razon_base}, acumulada)"
        push_propuesta_director({
            "citacion_id": c.id,
            "estudiante": str(est),
            "motivo": c.motivo_resumen,
            "razon": razon,
            "rho": None,
            "Wq": None,
            "sugerido": None,
        })
    except Exception:
        pass
