from django.db import migrations, models
from django.utils import timezone

class Migration(migrations.Migration):

    dependencies = [
        ("estudiantes", "0002_kardexitem_uq_kdx_item"),
    ]

    operations = [
        # Cambios de tamaño para acomodar choices nuevos
        migrations.AlterField(
            model_name="kardexitem",
            name="area",
            field=models.CharField("Área", max_length=16, choices=[
                ("SER","SER"),("SABER","SABER"),("HACER","HACER"),("DECIDIR","DECIDIR")
            ]),
        ),
        migrations.AlterField(
            model_name="kardexitem",
            name="sentido",
            field=models.CharField("Sentido", max_length=16, choices=[
                ("POSITIVO","Positivo"),("NEGATIVO","Negativo")
            ], default="NEGATIVO"),
        ),

        # ====== CAMPOS NUEVOS ======
        migrations.AddField(
            model_name="kardexitem",
            name="peso",
            field=models.PositiveSmallIntegerField(
                "Peso (severidad)", default=10,
                help_text="Severidad base: p.ej., 5 (leve), 10 (mod.), 20 (import.), 35 (grave).",
            ),
        ),
        migrations.AddField(
            model_name="kardexitem",
            name="ventana_dias",
            field=models.PositiveSmallIntegerField(
                "Ventana (días)", default=14,
                help_text="Período para contar recurrencias del mismo ítem.",
            ),
        ),
        migrations.AddField(
            model_name="kardexitem",
            name="umbral",
            field=models.PositiveSmallIntegerField(
                "Umbral (repeticiones)", default=0,
                help_text="Cantidad dentro de la ventana para disparar citación (0 = sin acumulación).",
            ),
        ),
        migrations.AddField(
            model_name="kardexitem",
            name="directa",
            field=models.BooleanField(
                "Citación directa", default=False,
                help_text="Si es True, un solo evento crea citación (Abierta).",
            ),
        ),
        migrations.AddField(
            model_name="kardexitem",
            name="activo",
            field=models.BooleanField("Activo", default=True),
        ),
        migrations.AddField(
            model_name="kardexitem",
            name="creado_en",
            field=models.DateTimeField("Creado en", auto_now_add=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="kardexitem",
            name="actualizado_en",
            field=models.DateTimeField("Actualizado en", auto_now=True, default=timezone.now),
            preserve_default=False,
        ),

        # Índice útil (no choca con el constraint uq_kdx_item ya existente)
        migrations.AddIndex(
            model_name="kardexitem",
            index=models.Index(fields=["area", "sentido", "activo"], name="estudian_kdx_idx"),
        ),
    ]
