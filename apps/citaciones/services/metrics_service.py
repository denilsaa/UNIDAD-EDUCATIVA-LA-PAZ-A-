# apps/citaciones/services/metrics_service.py
from datetime import timedelta
from django.utils.timezone import now
from apps.citaciones.models.citacion import Citacion
from apps.citaciones.models.config import AtencionConfig


def mu_from_config(cfg: AtencionConfig) -> float:
    return 60.0 / float(cfg.minutos_por_slot or 15)


def lambda_reciente(dias: int = 7) -> float:
    """
    Tasa de llegada por hora: citaciones creadas en 'dias' recientes.
    Aproximamos 8 horas laborales por día.
    """
    if dias <= 0:
        dias = 7
    base = now() - timedelta(days=dias)
    llegadas = Citacion.objects.filter(creado_en__gte=base).count()
    horas = dias * 8.0
    return (llegadas / horas) if horas else 0.0


def mm1(mu: float, lam: float) -> dict:
    if mu <= 0:
        return {"rho": 0.0, "Wq": None, "Ws": None, "saturada": True}
    rho = lam / mu
    if lam >= mu:
        return {"rho": rho, "Wq": None, "Ws": None, "saturada": True}
    Wq = rho / (mu - lam)   # horas
    Ws = 1.0 / (mu - lam)   # horas
    return {"rho": rho, "Wq": Wq, "Ws": Ws, "saturada": False}


def metrics_payload() -> dict:
    cfg = AtencionConfig.objects.first()
    mu = mu_from_config(cfg) if cfg else 0.0
    lam = lambda_reciente(7)
    m = mm1(mu, lam)
    m.update({"mu": mu, "lambda": lam})
    return m
