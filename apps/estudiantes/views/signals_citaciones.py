# apps/estudiantes/signals_citaciones.py
from __future__ import annotations
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.apps import apps as django_apps
from django.db import transaction

# Utilidad flexible: intenta detectar “negativo” con distintos campos
def _es_negativo(registro) -> bool:
    """
    Heurística: ajusta a tu modelo real.
    - Si KardexRegistro tiene campo 'es_negativo' o 'es_positivo'
    - O si KardexItem tiene 'peso' (<=0 o >0), o 'es_negativo'
    """
    if hasattr(registro, "es_negativo"):
        return bool(getattr(registro, "es_negativo"))
    if hasattr(registro, "es_positivo"):
        return not bool(getattr(registro, "es_positivo"))
    item = getattr(registro, "kardex_item", None)
    if item is not None:
        if hasattr(item, "es_negativo"):
            return bool(getattr(item, "es_negativo"))
        if hasattr(item, "peso"):
            try:
                return float(getattr(item, "peso") or 0) > 0  # según tu diseño; cambia a <=0 si aplica
            except Exception:
                return True
    return True  # por defecto trátalo como negativo

@receiver(post_save, sender=lambda: django_apps.get_model("estudiantes", "KardexRegistro"))
def kardex_registro_post_save(sender, instance, created, **kwargs):
    """
    Si el KardexRegistro es NEGATIVO y no ha generado citación aún,
    evaluamos reglas y potencialmente creamos Citacion ABIERTA (idempotente).
    """
    if not created:
        return
    if not _es_negativo(instance):
        return

    # Idempotencia por OneToOne (si ya está enlazado, no hacemos nada)
    if getattr(instance, "citacion", None):
        return

    RulesService = django_apps.get_model("citaciones", "Citacion")  # dummy para validar app cargada
    # Llamamos al service (import tardío para evitar import cycles)
    from apps.citaciones.services.rules_service import evaluar_kardex

    # En una transacción por si hay validaciones posteriores
    with transaction.atomic():
        evaluar_kardex(instance, ahora=timezone.now())
