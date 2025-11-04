# apps/citaciones/services/agenda_service.py
from datetime import datetime, timedelta, time
from django.utils.timezone import localdate
from apps.citaciones.models.config import AtencionConfig
from apps.citaciones.models.citacion import Citacion

HABILES = {0, 1, 2, 3, 4}  # L-V


def _cfg() -> AtencionConfig:
    return AtencionConfig.objects.first()


def _es_habil(d):
    return d.weekday() in HABILES


def _rangohoras(cfg: AtencionConfig):
    return cfg.hora_inicio, cfg.hora_fin


def _hay_choque(fecha, hora):
    # Choque básico: misma hora exacta en el mismo día (AGENDADA o NOTIFICADA)
    return Citacion.objects.filter(
        fecha_citacion=fecha,
        hora_citacion=hora,
        estado__in=[Citacion.Estado.AGENDADA, Citacion.Estado.NOTIFICADA],
    ).exists()


def next_free_slot(duracion_min: int | None = None, desde: datetime | None = None):
    cfg = _cfg()
    if not cfg:
        raise RuntimeError("AtencionConfig no configurado")

    if duracion_min is None:
        duracion_min = int(cfg.duracion_por_defecto)

    dt = desde or datetime.now()
    d = localdate() if desde is None else dt.date()
    hi, hf = _rangohoras(cfg)
    slot_min = int(cfg.minutos_por_slot)

    # Inicia hoy desde ahora (redondeado a slot) o desde hi
    if dt.date() == d:
        mm_now = dt.hour * 60 + dt.minute
        mm_slot = ((mm_now + slot_min - 1) // slot_min) * slot_min
        t_inicio = max(time(mm_slot // 60, mm_slot % 60), hi)
    else:
        t_inicio = hi

    dias_vistos = 0
    while dias_vistos <= int(cfg.max_dias):
        if _es_habil(d):
            h = t_inicio
            while h < hf:
                if not _hay_choque(d, h):
                    return d, h
                mm = (h.hour * 60 + h.minute) + slot_min
                h = time(mm // 60, mm % 60)
        d = d + timedelta(days=1)
        t_inicio = hi
        dias_vistos += 1

    raise RuntimeError("No hay slots libres dentro de la ventana")


def agendar(citacion: Citacion, duracion_min: int | None = None) -> Citacion:
    fecha, hora = next_free_slot(duracion_min)
    citacion.fecha_citacion = fecha
    citacion.hora_citacion = hora
    citacion.estado = Citacion.Estado.AGENDADA
    citacion.save(update_fields=["fecha_citacion", "hora_citacion", "estado", "actualizado_en"])
    return citacion
