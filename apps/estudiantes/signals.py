from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date

from apps.estudiantes.models.estudiante import Estudiante
from apps.cursos.models.kardex import Kardex

def trimestre_actual(hoy: date) -> int:
    # Adapte a su calendario (3 trimestres o 4 bimestres, etc.)
    if hoy.month <= 4:
        return 1
    if hoy.month <= 8:
        return 2
    return 3

@receiver(post_save, sender=Estudiante)
def asignar_kardex_automatico(sender, instance: Estudiante, created, **kwargs):
    """Al crear un estudiante, buscar/crear Kardex del curso en el periodo y asignarlo."""
    if not created or not instance.curso_id:
        return

    hoy = date.today()
    kdx, _ = Kardex.objects.get_or_create(
        curso=instance.curso,
        anio=hoy.year,
        trimestre=trimestre_actual(hoy),
        defaults={"observacion": ""},
    )
    # evitar recursion: actualice por query
    Estudiante.objects.filter(pk=instance.pk).update(kardex=kdx)
