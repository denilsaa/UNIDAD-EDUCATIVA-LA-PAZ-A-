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


# ==========================
#  Helpers de solapamiento
# ==========================
def _to_min(t: time) -> int:
    """Convierte un time a minutos desde las 00:00."""
    return t.hour * 60 + t.minute


def _hay_choque(fecha, hora: time, duracion_min: int) -> bool:
    """
    Devuelve True si el intervalo [hora, hora+duracion) se solapa
    con alguna citación ya AGENDADA/NOTIFICADA de ese día.
    """
    cfg = _cfg()
    dur = int(duracion_min or cfg.duracion_por_defecto)

    inicio_nuevo = _to_min(hora)
    fin_nuevo = inicio_nuevo + dur

    existentes = Citacion.objects.filter(
        fecha_citacion=fecha,
        estado__in=[Citacion.Estado.AGENDADA, Citacion.Estado.NOTIFICADA],
    ).only("hora_citacion", "duracion_min")

    for c in existentes:
        d = int(c.duracion_min or cfg.duracion_por_defecto)
        inicio = _to_min(c.hora_citacion)
        fin = inicio + d
        # Se solapan si NO (nuevo termina antes de empezar el otro) y NO (nuevo empieza después de que el otro termine)
        if not (fin_nuevo <= inicio or inicio_nuevo >= fin):
            return True
    return False


# ==========================
#  Búsqueda de slot libre
# ==========================
def next_free_slot(duracion_min: int | None = None, desde: datetime | None = None):
    """
    Busca el siguiente slot disponible respetando:
    - Lunes a viernes
    - Ventana hora_inicio / hora_fin
    - Tamaño de slot (minutos_por_slot)
    - SIN solapamientos por duración
    """
    cfg = _cfg()
    if not cfg:
        raise RuntimeError("AtencionConfig no configurado")

    dur = int(duracion_min or cfg.duracion_por_defecto)

    dt = desde or datetime.now()
    d = localdate() if desde is None else dt.date()
    hi, hf = _rangohoras(cfg)
    slot_min = int(cfg.minutos_por_slot)

    # Límite del día en minutos (para que quepa la duración completa)
    hf_min = _to_min(hf)

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
            while True:
                # Si el fin se pasa del horario de fin, deja de probar en este día
                if _to_min(h) + dur > hf_min:
                    break
                # Verifica superposición real por duración
                if not _hay_choque(d, h, dur):
                    return d, h
                # Avanza al siguiente slot
                mm = _to_min(h) + slot_min
                h = time(mm // 60, mm % 60)
        # Siguiente día hábil
        d = d + timedelta(days=1)
        t_inicio = hi
        dias_vistos += 1

    raise RuntimeError("No hay slots libres dentro de la ventana")


def agendar(citacion: Citacion, duracion_min: int | None = None) -> Citacion:
    """
    Asigna la primera fecha/hora libre y marca como AGENDADA.
    """
    fecha, hora = next_free_slot(duracion_min)
    citacion.fecha_citacion = fecha
    citacion.hora_citacion = hora
    citacion.estado = Citacion.Estado.AGENDADA
    citacion.save(update_fields=["fecha_citacion", "hora_citacion", "estado", "actualizado_en"])
    return citacion


def suggest_free_slot(duracion_min: int | None = None):
    """
    Igual que next_free_slot() pero solo devuelve (fecha, hora) sin tocar la BD.
    """
    return next_free_slot(duracion_min=duracion_min, desde=None)
