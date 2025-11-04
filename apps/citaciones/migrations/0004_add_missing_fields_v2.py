from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('citaciones', '0003_add_kardex_registro_fk'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # --- SOLO lo que falta con seguridad ---

        # 1) Motivo (resumen)
        migrations.AddField(
            model_name='citacion',
            name='motivo_resumen',
            field=models.CharField(
                verbose_name='Motivo (resumen)',
                max_length=160,
                blank=True,
                default='',
            ),
        ),

        # 2) Duración (min)
        migrations.AddField(
            model_name='citacion',
            name='duracion_min',
            field=models.PositiveSmallIntegerField(
                verbose_name='Duración (minutos)',
                default=30,
                help_text='15, 30, 45 o 60. Se usa para agenda y métricas.',
            ),
        ),

        # 3) Aprobación (FK a usuario, fecha)
        migrations.AddField(
            model_name='citacion',
            name='aprobado_por',
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
                blank=True,
                related_name='citaciones_aprobadas',
                verbose_name='Aprobado por',
            ),
        ),
        migrations.AddField(
            model_name='citacion',
            name='aprobado_en',
            field=models.DateTimeField(
                verbose_name='Aprobado en',
                null=True,
                blank=True,
            ),
        ),

        # ⚠️ OJO: NO agregar fecha_citacion ni hora_citacion aquí
        # porque en tu BD ya existen y causan "Duplicate column".
    ]
