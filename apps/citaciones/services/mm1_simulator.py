# apps/citaciones/services/mm1_simulator.py

from datetime import timedelta

from django.utils import timezone
from django.db.models import Count

from apps.citaciones.models import Citacion, AtencionConfig
from apps.citaciones.services.metrics_service import mm1


def lambda_desde_bd(dias: int = 7) -> float:
    """
    Calcula λ (tasa de llegada de citaciones por hora) usando la tabla Citacion
    en un rango de 'dias' hacia atrás.
    """
    ahora = timezone.now()
    inicio = ahora - timedelta(days=dias)

    qs = Citacion.objects.filter(creado_en__gte=inicio, creado_en__lte=ahora)
    total = qs.count()
    if total == 0:
        return 0.0

    delta_horas = (ahora - inicio).total_seconds() / 3600
    return total / delta_horas


def mu_desde_config() -> float:
    """
    Calcula μ (tasa de servicio) a partir de la configuración de atención.
    Supone que AtencionConfig tiene un campo 'minutos_por_slot'.
    """
    cfg = AtencionConfig.objects.first()
    if not cfg or not cfg.minutos_por_slot:
        return 0.0

    slot_horas = cfg.minutos_por_slot / 60.0
    return 1.0 / slot_horas  # casos por hora


def simulacion_mm1(dias: int = 7) -> dict:
    """
    Simula el modelo M/M/1 usando λ calculado desde BD y μ desde configuración.
    Devuelve todas las métricas, incluyendo tiempos en minutos.
    """
    lam = lambda_desde_bd(dias=dias)
    mu = mu_desde_config()

    m = mm1(mu, lam)  # rho, Wq, Ws, saturada

    # convertir tiempos de horas a minutos
    Wq_min = m["Wq"] * 60 if m["Wq"] is not None else None
    Ws_min = m["Ws"] * 60 if m["Ws"] is not None else None

    m.update({
        "lambda": lam,
        "mu": mu,
        "Wq_min": Wq_min,
        "Ws_min": Ws_min,
    })
    return m


def distribucion_por_estado() -> dict:
    """
    Devuelve la cantidad de citaciones agrupadas por estado
    (por ejemplo: pendiente, aprobada, atendida, cancelada).
    """
    qs = (
        Citacion.objects
        .values("estado")
        .annotate(total=Count("id"))
        .order_by("estado")
    )

    labels = []
    data = []

    for row in qs:
        etiqueta = row["estado"] or "Sin estado"
        labels.append(etiqueta)
        data.append(row["total"])

    return {
        "labels": labels,
        "data": data,
    }
