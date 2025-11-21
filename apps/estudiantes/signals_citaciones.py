from datetime import timedelta

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now

from apps.estudiantes.models.kardex_registro import KardexRegistro
from apps.citaciones.models.citacion import Citacion

# (Opcional) notificación por WS; si no está, no romper
try:
    from apps.citaciones.ws import push_propuesta_director
except Exception:  # en tests/ambientes sin WS
    def push_propuesta_director(_payload):
        # En entornos donde no haya WebSockets configurados simplemente no hacemos nada
        return


def _obtener_o_acumular_citacion(estudiante, kdx_registro, motivo_txt, duracion_base=30):
    """
    Reutiliza una citación pendiente del estudiante (si ya tiene una
    PARA EL MISMO DÍA del registro de kárdex), acumulando:
      - la duración (duracion_min)
      - el texto del motivo (motivo_resumen)

    Si no existe citación para ese día, crea una nueva.

    Idea M/M/1: para un mismo día y estudiante tenemos un solo "cliente"
    en la cola, pero con mayor tiempo de servicio.
    """
    motivo_txt = (motivo_txt or "").strip()

    with transaction.atomic():
        # Buscar citación del mismo estudiante y MISMO DÍA del kardex_registro
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
                kardex_registro__fecha=kdx_registro.fecha,  # 👈 clave: mismo día
            )
            .order_by("creado_en")
            .first()
        )

        if existente is not None:
            # --- ACUMULAR EN LA EXISTENTE ---
            existente.duracion_min = (existente.duracion_min or 0) + int(duracion_base or 0)

            if motivo_txt:
                if existente.motivo_resumen:
                    # Evitar repetir exactamente el mismo texto muchas veces
                    if motivo_txt not in existente.motivo_resumen:
                        existente.motivo_resumen = (
                            f"{existente.motivo_resumen}; {motivo_txt}"
                        )[:160]
                else:
                    existente.motivo_resumen = motivo_txt[:160]

            existente.save(update_fields=["duracion_min", "motivo_resumen", "actualizado_en"])
            return existente, False

        # --- NO HABÍA CITACIÓN PARA ESE DÍA → CREAMOS UNA NUEVA ---
        nueva = Citacion.objects.create(
            estudiante=estudiante,
            kardex_registro=kdx_registro,
            motivo_resumen=motivo_txt[:160] if motivo_txt else "",
            estado=Citacion.Estado.ABIERTA,
            duracion_min=int(duracion_base or 0) or 30,
        )
        return nueva, True


@receiver(post_save, sender=KardexRegistro)
def generar_citacion_desde_kardex(sender, instance: KardexRegistro, created, **kwargs):
    """
    Signal que se dispara cada vez que se crea un KardexRegistro.

    Aplica dos tipos de regla:

      1) Citación DIRECTA (campo `directa` del KardexItem)
      2) Citación por ACUMULACIÓN (campos `umbral` y `ventana_dias`)

    En ambos casos, si el estudiante ya tiene una citación
    ABIERTA / AGENDADA / NOTIFICADA para el MISMO DÍA,
    no se crea una nueva, sino que se acumula duración y motivo
    en la existente.
    """
    if not created:
        return

    est = instance.estudiante
    item = instance.kardex_item

    # Texto base del motivo (puedes ajustarlo si usas otro campo)
    motivo_txt = str(item)

    # ------------------------------------------------------------------
    # 1) REGLA DIRECTA
    # ------------------------------------------------------------------
    directa = bool(getattr(item, "directa", False))
    if directa:
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
            # No queremos que un fallo de WS rompa el flujo
            pass

        # Si es directa, no seguimos con acumulación
        return

    # ------------------------------------------------------------------
    # 2) REGLA POR ACUMULACIÓN
    # ------------------------------------------------------------------
    umbral = int(getattr(item, "umbral", 0) or 0)
    ventana = int(getattr(item, "ventana_dias", 0) or 0)

    if umbral <= 0:
        return

    if ventana <= 0 or ventana > 15:
        ventana = 15

    hoy = now().date()
    desde = hoy - timedelta(days=ventana)

    # Cuántos registros de este ítem tiene el estudiante en la ventana
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
