# apps/citaciones/services/queue_service.py
from datetime import timedelta, datetime
from django.db.models import Avg, F, DurationField, ExpressionWrapper
from django.utils.timezone import now, get_current_timezone
from ..models.queue import QueueItem
from ..models.config import AtencionConfig

def mm1_estimaciones(ventana_min=60):
    """
    λ̂: llegadas/min = QueueItems (aprobadas) creados en la última hora / 60
    μ̂: servicios/min = 1 / E[duración] (si no hay histórico, 1/duración_por_defecto)
    """
    t = now()
    hace = t - timedelta(minutes=ventana_min)
    # λ̂ (solo aprobadas: ya tienen QueueItem)
    lambda_hat = QueueItem.objects.filter(creado_en__gte=hace).count() / float(ventana_min)

    # μ̂
    atendidas = QueueItem.objects.exclude(inicio_servicio_en=None).exclude(fin_servicio_en=None)
    if atendidas.exists():
        avg = atendidas.annotate(
            dur=ExpressionWrapper(F("fin_servicio_en") - F("inicio_servicio_en"),
                                  output_field=DurationField())
        ).aggregate(avg=Avg("dur"))["avg"]
        mu_hat = (60.0 / max((avg.total_seconds() / 60.0), 1.0)) if avg else None
    else:
        mu_hat = None

    # fallback μ̂ por config
    if not mu_hat:
        try:
            cfg = AtencionConfig.objects.latest("creado_en")
            mu_hat = 1.0 / max(getattr(cfg, "duracion_por_defecto", 30), 1)
        except Exception:
            mu_hat = 1.0 / 30.0

    rho = lambda_hat / mu_hat if mu_hat > 0 else 0.0
    if rho >= 1.0:
        return dict(lambda_hat=lambda_hat, mu_hat=mu_hat, rho=rho, Wq=None, Ws=None)

    Wq = rho / (mu_hat - lambda_hat) if mu_hat > lambda_hat else None
    Ws = 1.0 / (mu_hat - lambda_hat) if mu_hat > lambda_hat else None
    return dict(lambda_hat=lambda_hat, mu_hat=mu_hat, rho=rho, Wq=Wq, Ws=Ws)

def _es_fin_de_semana(dt):
    # 5=sábado, 6=domingo
    return dt.weekday() >= 5

def _proximo_laboral(dt):
    # si cae sábado o domingo, mover a lunes 08:00
    while _es_fin_de_semana(dt):
        dt = dt + timedelta(days=1)
        dt = dt.replace(hour=8, minute=0, second=0, microsecond=0)
    return dt

def _alinear_a_slot(cfg, dt):
    tz = get_current_timezone()
    dt = dt.astimezone(tz).replace(second=0, microsecond=0)

    # si cae fin de semana, a lunes 08:00
    dt = _proximo_laboral(dt)

    # ventana diaria
    inicio = dt.replace(hour=cfg.hora_inicio.hour, minute=cfg.hora_inicio.minute)
    fin = dt.replace(hour=cfg.hora_fin.hour, minute=cfg.hora_fin.minute)

    # si antes de inicio → a inicio; si después de fin → al día siguiente a inicio
    if dt < inicio:
        dt = inicio
    elif dt >= fin:
        dt = (inicio + timedelta(days=1)).replace(second=0, microsecond=0)
        dt = _proximo_laboral(dt)

    # snap al múltiplo del slot
    minutos = int((dt - inicio).total_seconds() // 60)
    resto = minutos % cfg.minutos_por_slot
    if resto:
        dt = dt + timedelta(minutes=(cfg.minutos_por_slot - resto))
    return dt

def sugerir_slot_por_mm1(base_dt=None):
    """
    Devuelve (estimaciones, dt_sugerido) sin modificar DB.
    """
    est = mm1_estimaciones()
    try:
        cfg = AtencionConfig.objects.latest("creado_en")
    except Exception:
        # defaults defensivos
        class _Cfg: pass
        cfg = _Cfg()
        cfg.hora_inicio = datetime.now().replace(hour=8, minute=0)
        cfg.hora_fin = datetime.now().replace(hour=12, minute=0)
        cfg.minutos_por_slot = 15
        cfg.duracion_por_defecto = 30
        cfg.max_dias_agenda = 7

    base = base_dt or now()
    if est["Wq"] is None:
        dt = _alinear_a_slot(cfg, base)
    else:
        dt = _alinear_a_slot(cfg, base + timedelta(minutes=est["Wq"]))

    # respetar máx 7 días
    limite = base + timedelta(days=int(getattr(cfg, "max_dias_agenda", 7)))
    if dt > limite:
        dt = _alinear_a_slot(cfg, limite.replace(hour=8, minute=0))
    return est, dt
