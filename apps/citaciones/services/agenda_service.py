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
        ini_exist, fin_exist = _ocupa_rango(c.hora_citacion, int(c.duracion_min or 30))
        if _se_solapa(ini_nuevo, fin_nuevo, ini_exist, fin_exist):
            return True
    return False


# ======================
#  Búsqueda de huecos
# ======================
def next_free_slot(duracion_min: int | None = None, desde: datetime | None = None):
    """
    Busca el siguiente hueco libre a partir de hoy (o de `desde`)
    respetando la configuración de atención y las citaciones ya agendadas.

    Retorna: (fecha, hora)
    """
    cfg = _cfg()
    if cfg is None:
        # Valores por defecto si no hay configuración
        duracion_min = duracion_min or 30
        hoy = localdate()
        return hoy, time(8, 0)

    duracion_min = duracion_min or int(cfg.duracion_por_defecto or 30)

    hoy = localdate()
    if desde is not None:
        # si se nos pasa un datetime de referencia, arrancamos desde ahí
        hoy = desde.date()

    fecha = hoy
    while True:
        if not _es_habil(fecha):
            fecha += timedelta(days=1)
            continue

        hi, hf = _rangohoras(cfg)
        hf_min = _to_min(hf)

        # Empezar desde el inicio o desde la hora sugerida por `desde`
        if desde is not None and fecha == desde.date():
            current_min = max(_to_min(hi), _to_min(desde.time()))
        else:
            current_min = _to_min(hi)

        while current_min + duracion_min <= hf_min:
            h = time(current_min // 60, current_min % 60)
            if not _hay_solape(fecha, h, duracion_min):
                return fecha, h
            current_min += cfg.slot_min or 5

        fecha += timedelta(days=1)


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
    else:
        hora_inicio = getattr(cfg, "hora_inicio", time(8, 0))
        hora_fin = getattr(cfg, "hora_fin", time(12, 0))

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
        dur = int(c.duracion_min or getattr(cfg, "duracion_por_defecto", 30))
        # si ya no cabe en el día, salimos (opcional: podrías mandarla al día siguiente)
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
