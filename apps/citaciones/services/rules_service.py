# apps/citaciones/services/rules_service.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from django.apps import apps as django_apps
from django.utils import timezone

@dataclass
class ResultadoRegla:
    creada: bool
    motivo: str
    citacion_id: Optional[int] = None

def _tz_now_lapaz(ahora=None):
    # Si pasas 'ahora' (tests), lo respeta; sino usa now()
    return ahora or timezone.now()

def _resumen_motivo_directa(kdx_registro) -> str:
    # Resume algo útil para UI (ajusta a tus campos reales)
    item = getattr(kdx_registro, "kardex_item", None)
    item_nombre = getattr(item, "nombre", "Ítem negativo")
    return f"Directa por ítem: {item_nombre}"

def _es_directa(kdx_registro) -> bool:
    item = getattr(kdx_registro, "kardex_item", None)
    # ✅ Usa tu campo existente "sentido": si es NEGATIVO, lo tratamos como directa (para probar)
    sentido = (getattr(item, "sentido", "") or "").strip().lower()
    return sentido.startswith("neg")  # "Negativo", "negativo"


def _cumple_acumulacion(kdx_registro, ahora) -> bool:
    """
    TODO (fase siguiente): contar ocurrencias del mismo ítem en ventana_dias >= umbral.
    Por ahora devolvemos False y dejamos sólo Directa funcionando.
    """
    return False

def _cumple_transversal(kdx_registro, ahora) -> bool:
    """
    TODO (fase siguiente): suma de pesos en ventana de N días >= umbral
    si ReglaTransversalConfig.habilitada y vigente_desde <= ahora.
    """
    return False

def _crear_citacion_abierta(kdx_registro, motivo_resumen: str, ahora):
    Citacion = django_apps.get_model("citaciones", "Citacion")
    # Evita duplicar si ya existe (idempotencia por OneToOne)
    if getattr(kdx_registro, "citacion", None):
        return kdx_registro.citacion

    # Campos clave según tu BD actual
    cit = Citacion.objects.create(
        estudiante=kdx_registro.estudiante,
        kardex_registro=kdx_registro,
        fecha_citacion=None,
        hora_citacion=None,
        duracion_min=None,
        aprobado_por=None,
        aprobado_en=None,
        motivo_resumen=motivo_resumen,
        estado="ABIERTA",   # usa tu Choice real si aplica
        creada_en=ahora if hasattr(Citacion, "creada_en") else None,
    )
    return cit

def evaluar_kardex(kdx_registro, ahora=None) -> ResultadoRegla:
    """
    Regla mínima (V1):
      - Si el ítem tiene flag_directa=True => crea Citación ABIERTA
      - (Acumulación y Transversal quedan para el siguiente paso)
    Garantiza idempotencia (OneToOne en kardex_registro).
    """
    ahora = _tz_now_lapaz(ahora)
    if _es_directa(kdx_registro):
        motivo = _resumen_motivo_directa(kdx_registro)
        cit = _crear_citacion_abierta(kdx_registro, motivo, ahora)
        return ResultadoRegla(creada=True, motivo="directa", citacion_id=cit.id)

    if _cumple_acumulacion(kdx_registro, ahora):
        # TODO: completar en siguiente fase
        motivo = "Acumulación de ítems (TODO)"
        cit = _crear_citacion_abierta(kdx_registro, motivo, ahora)
        return ResultadoRegla(creada=True, motivo="acumulacion", citacion_id=cit.id)

    if _cumple_transversal(kdx_registro, ahora):
        # TODO: completar en siguiente fase
        motivo = "Transversal (TODO)"
        cit = _crear_citacion_abierta(kdx_registro, motivo, ahora)
        return ResultadoRegla(creada=True, motivo="transversal", citacion_id=cit.id)

    return ResultadoRegla(creada=False, motivo="no_aplica", citacion_id=None)
