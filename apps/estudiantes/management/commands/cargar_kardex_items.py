from django.core.management.base import BaseCommand
from apps.estudiantes.models.kardex_item import KardexItem

DATOS = [
    ("SER","Atrasos","NEGATIVO"),
    ("SER","Faltas sin licencia","NEGATIVO"),
    ("SER","Irrespeto a profesores o compañeros","NEGATIVO"),
    ("SER","No porta uniforme correspondiente del colegio","NEGATIVO"),
    ("SER","Usa celular, audífonos u otros en clases","NEGATIVO"),
    ("SER","Indisciplinado(a) en aula","NEGATIVO"),
    ("SER","Violencia (física/verbal)","NEGATIVO"),
    ("SABER","No se presentó a la evaluación","NEGATIVO"),
    ("SABER","Realiza fraude en las evaluaciones","NEGATIVO"),
    ("SABER","Desinterés en el aprendizaje teórico-práctico","NEGATIVO"),
    ("SABER","No se presentó a la exposición y/o defensa de un trabajo","NEGATIVO"),
    ("SABER","Bajo rendimiento en las evaluaciones","NEGATIVO"),
    ("HACER","No realiza tareas asignadas en casa","NEGATIVO"),
    ("HACER","No realiza las actividades en aula","NEGATIVO"),
    ("HACER","No porta material para el trabajo en aula","NEGATIVO"),
    ("HACER","Presenta tareas incorrectamente","NEGATIVO"),
    ("HACER","Desorden en la presentación de cuadernos y/o trabajos","NEGATIVO"),
    ("DECIDIR","No participa en diversas actividades educativas","NEGATIVO"),
    ("DECIDIR","Demuestra desinterés y poca iniciativa en el área","NEGATIVO"),
    ("DECIDIR","Necesita compromiso en trabajos en equipo/clubes","NEGATIVO"),
    ("DECIDIR","Poco contribuye con opiniones/observaciones críticas","NEGATIVO"),
    ("DECIDIR","No asume decisiones para solucionar problemáticas","NEGATIVO"),
]

class Command(BaseCommand):
    help = "Carga los ítems iniciales del kárdex"

    def handle(self, *args, **kwargs):
        creados = 0
        for area, desc, sentido in DATOS:
            _, was_created = KardexItem.objects.get_or_create(
                area=area, descripcion=desc, sentido=sentido
            )
            creados += int(was_created)
        self.stdout.write(self.style.SUCCESS(f"Ítems verificados. Nuevos creados: {creados}"))
