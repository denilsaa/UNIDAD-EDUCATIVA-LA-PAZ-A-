from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    # 👇 AJUSTA el segundo elemento ('citaciones', '0001_initial') a tu última migración real de citaciones
    dependencies = [
        ('estudiantes', '0002_kardexitem_uq_kdx_item'),
        ('citaciones', '0002_fix_missing_tables'),  # <-- antes apuntaba a 0001_initial
    ]

    operations = [
        migrations.AddField(
            model_name='citacion',
            name='kardex_registro',
            field=models.OneToOneField(
                to='estudiantes.kardexregistro',
                on_delete=django.db.models.deletion.RESTRICT,
                related_name='citacion_origen',
                verbose_name='Registro de Kárdex',
                null=True,
                blank=True,
            ),
        ),
    ]
