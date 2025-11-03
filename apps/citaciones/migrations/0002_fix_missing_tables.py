from django.db import migrations, models
import datetime
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ("citaciones", "0001_initial"),
    ]

    operations = [
        # Creamos las tablas faltantes a nivel BD, pero sin alterar el "state" que Django cree
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.CreateModel(
                    name="AtencionConfig",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("hora_inicio", models.TimeField(default=datetime.time(8, 0), verbose_name="Hora de inicio")),
                        ("hora_fin", models.TimeField(default=datetime.time(12, 0), verbose_name="Hora de fin")),
                        ("minutos_por_slot", models.PositiveSmallIntegerField(default=15, verbose_name="Minutos por slot")),
                        ("duracion_por_defecto", models.PositiveSmallIntegerField(default=30, verbose_name="Duración por defecto (min)")),
                        ("max_dias", models.PositiveSmallIntegerField(default=7, verbose_name="Días máximos para agendar")),
                        ("creado_en", models.DateTimeField(auto_now_add=True, verbose_name="Creado en")),
                        ("actualizado_en", models.DateTimeField(auto_now=True, verbose_name="Actualizado en")),
                    ],
                    options={
                        "verbose_name": "configuración de atención",
                        "verbose_name_plural": "configuraciones de atención",
                    },
                ),
                migrations.CreateModel(
                    name="ReglaTransversalConfig",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("habilitada", models.BooleanField(default=True, verbose_name="Habilitada")),
                        ("umbral", models.PositiveSmallIntegerField(default=35, verbose_name="Umbral de suma")),
                        ("ventana_dias", models.PositiveSmallIntegerField(default=14, verbose_name="Ventana (días)")),
                        ("programada", models.BooleanField(default=False, verbose_name="Programada")),
                        ("vigente_desde", models.DateTimeField(blank=True, null=True, verbose_name="Vigente desde")),
                        ("historial_json", models.TextField(blank=True, default="[]", verbose_name="Historial (JSON)")),
                        ("creado_en", models.DateTimeField(auto_now_add=True, verbose_name="Creado en")),
                        ("actualizado_en", models.DateTimeField(auto_now=True, verbose_name="Actualizado en")),
                    ],
                    options={
                        "verbose_name": "configuración de regla transversal",
                        "verbose_name_plural": "configuraciones de regla transversal",
                    },
                ),
                migrations.CreateModel(
                    name="QueueItem",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("estado", models.CharField(choices=[("EN_COLA", "En cola"), ("EN_SERVICIO", "En servicio"), ("ATENDIDA", "Atendida"), ("FALLIDA", "Fallida")], default="EN_COLA", max_length=12, verbose_name="Estado en cola")),
                        ("llegada_en", models.DateTimeField(auto_now_add=True, verbose_name="Llegó a la cola")),
                        ("inicio_servicio_en", models.DateTimeField(blank=True, null=True, verbose_name="Inicio de atención")),
                        ("fin_servicio_en", models.DateTimeField(blank=True, null=True, verbose_name="Fin de atención")),
                        ("creado_en", models.DateTimeField(auto_now_add=True, verbose_name="Creado en")),
                        ("actualizado_en", models.DateTimeField(auto_now=True, verbose_name="Actualizado en")),
                        ("citacion", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="queue_item", to="citaciones.citacion", verbose_name="Citación")),
                    ],
                    options={
                        "verbose_name": "ítem de cola",
                        "verbose_name_plural": "ítems de cola",
                        "ordering": ["llegada_en"],
                    },
                ),
            ],
            state_operations=[
                # No tocamos el "state" (Django ya cree que existen por 0001),
                # así evitamos inconsistencias con el loader de modelos.
            ],
        ),
    ]
