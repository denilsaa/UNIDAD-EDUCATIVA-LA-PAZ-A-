# apps/citaciones/services/agenda_service.py
from datetime import datetime, timedelta, time

from django.utils.timezone import localdate, now

from apps.citaciones.models.config import AtencionConfig
from apps.citaciones.models.citacion import Citacion

HABILES = {0, 1, 2, 3, 4}  # L-V


def _cfg() -> AtencionConfig | None:
    return AtencionConfig.objects.first()


def _es_habil(d):
    return d.weekday() in HABILES


def _rangohoras(cfg: AtencionConfig):
    return cfg.hora_inicio, cfg.hora_fin


# ==========================
#  Helpers de solapamiento
# ==========================
def _to_min(t: time) -> int:
    return t.hour * 60 + t.minute


def _ocupa_rango(hora_ini: time, duracion_min: int) -> tuple[int, int]:
    ini = _to_min(hora_ini)
    fin = ini + duracion_min
    return ini, fin


def _se_solapa(ini1, fin1, ini2, fin2) -> bool:
    return not (fin1 <= ini2 or fin2 <= ini1)


def _hay_solape(fecha, hora_ini: time, duracion_min: int) -> bool:
    """
    ¿Hay alguna citación AGENDADA/NOTIFICADA ese día que se solape con
    [hora_ini, hora_ini+duracion]?
    """
    ini_nuevo, fin_nuevo = _ocupa_rango(hora_ini, duracion_min)
    qs = Citacion.objects.filter(
        fecha_citacion=fecha,
        estado__in=[Citacion.Estado.AGENDADA, Citacion.Estado.NOTIFICADA],
    )
    for c in qs:
        if not c.hora_citacion:
            continue
        ini_exist, fin_exist = _ocupa_rango(
            c.hora_citacion,
            int(c.duracion_min or 30),
        )
        if _se_solapa(ini_nuevo, fin_nuevo, ini_exist, fin_exist):
            return True
    return False


# ======================
#  Búsqueda de huecos
# ======================
def next_free_slot(duracion_min: int | None = None, desde: datetime | None = None):
    """
    Busca el siguiente hueco libre respetando:

    - Horario de atención configurado (hora_inicio, hora_fin)
    - Días hábiles (L-V)
    - Citaciones ya AGENDADAS/NOTIFICADAS (no solapar)
    - Momento actual: si ya pasó el horario de hoy, empieza desde el
      siguiente día hábil.

    Si `desde` es None, se toma como referencia la hora actual.
    Si `desde` tiene valor, se simula como si la citación llegara en ese instante.
    Retorna: (fecha, hora)
    """
    cfg = _cfg()
    if cfg is None:
        # Sin configuración: fallback básico
        duracion_min = duracion_min or 30
        ref = desde or now()
        return ref.date(), time(8, 0)

    # Duración por defecto si no se especifica
    duracion_min = duracion_min or int(
        getattr(cfg, "duracion_por_defecto", 30) or 30
    )

    # Punto de referencia: ahora mismo si no se pasa `desde`
    ref: datetime = desde or now()
    fecha_ref = ref.date()
    minutos_ref = ref.hour * 60 + ref.minute

    fecha = fecha_ref
    while True:
        # Saltar días no hábiles
        if not _es_habil(fecha):
            fecha += timedelta(days=1)
            continue

        hi, hf = _rangohoras(cfg)
        hi_min = _to_min(hi)
        hf_min = _to_min(hf)

        if fecha == fecha_ref:
            # Mismo día de la referencia:
            # - Si aún no empieza la jornada -> hora_inicio
            # - Si estamos dentro -> desde ahora
            # - Si ya pasó la jornada -> este día no sirve
            current_min = max(hi_min, minutos_ref)
        else:
            # Días siguientes empiezan en hora_inicio
            current_min = hi_min

        # Si ya no cabe en el día, pasar al siguiente hábil
        if current_min + duracion_min > hf_min:
            fecha += timedelta(days=1)
            continue

        # Buscar primer hueco libre de este día
        while current_min + duracion_min <= hf_min:
            h = time(current_min // 60, current_min % 60)

            # No solapar con citaciones ya agendadas/notificadas
            if not _hay_solape(fecha, h, duracion_min):
                return fecha, h

            # Avanzar por slots (minutos_por_slot)
            current_min += getattr(cfg, "minutos_por_slot", 5) or 5

        # Si no cupo en este día, intentar con el siguiente
        fecha += timedelta(days=1)


def agendar(citacion: Citacion, duracion_min: int | None = None) -> Citacion:
    """
    Asigna la primera fecha/hora libre y marca como AGENDADA.
    """
    fecha, hora = next_free_slot(duracion_min)
    citacion.fecha_citacion = fecha
    citacion.hora_citacion = hora
    citacion.estado = Citacion.Estado.AGENDADA
    citacion.save(
        update_fields=[
            "fecha_citacion",
            "hora_citacion",
            "estado",
            "actualizado_en",
        ]
    )
    return citacion


def reordenar_dia_por_peso(fecha):
    """
    Reordena todas las citaciones AGENDADAS/NOTIFICADAS de ese día
    para que las de MAYOR peso (duracion_min) vayan primero.

    No cambia la fecha_citacion, solo reajusta hora_citacion dentro del
    bloque horario definido en AtencionConfig.
    """
    if not fecha:
        return

    cfg = _cfg()
    if cfg is None:
        # valores por defecto si no hay config
        hora_inicio = time(8, 0)
        hora_fin = time(12, 0)
        dur_def = 30
    else:
        hora_inicio = getattr(cfg, "hora_inicio", time(8, 0))
        hora_fin = getattr(cfg, "hora_fin", time(12, 0))
        dur_def = getattr(cfg, "duracion_por_defecto", 30) or 30

    def _to_min_local(t: time) -> int:
        return t.hour * 60 + t.minute

    hi_min = _to_min_local(hora_inicio)
    hf_min = _to_min_local(hora_fin)

    # Todas las citaciones de ese día, ordenadas por mayor duración (PESO)
    citas = list(
        Citacion.objects.filter(
            fecha_citacion=fecha,
            estado__in=[Citacion.Estado.AGENDADA, Citacion.Estado.NOTIFICADA],
        ).order_by("-duracion_min", "creado_en")
    )
    if not citas:
        return

    # Vamos asignando horas una tras otra desde la hora de inicio
    current_min = hi_min
    for c in citas:
        dur = int(c.duracion_min or dur_def)
        # si ya no cabe en el día, salimos (opcional: podrías moverla al día siguiente)
        if current_min + dur > hf_min:
            break

        h = time(current_min // 60, current_min % 60)
        c.hora_citacion = h
        c.save(update_fields=["hora_citacion", "actualizado_en"])

        current_min += dur


def suggest_free_slot(duracion_min: int | None = None, desde: datetime | None = None):
    """
    Igual que next_free_slot() pero solo devuelve (fecha, hora) sin tocar la BD.

    Si se pasa `desde`, se simula la cola como si esta citación llegara a partir
    de ese instante (útil para calcular ETAs en la bandeja ordenada por peso).
    """
    return next_free_slot(duracion_min=duracion_min, desde=desde)
