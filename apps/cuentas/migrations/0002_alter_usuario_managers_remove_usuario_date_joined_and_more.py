from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('cuentas', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='usuario',
            managers=[  # Si no estás usando managers personalizados, puedes dejar esta lista vacía.
            ],
        ),
        # Comentar o eliminar las siguientes líneas si no deseas eliminar estos campos
        # migrations.RemoveField(
        #     model_name='usuario',
        #     name='date_joined',
        # ),
        # migrations.RemoveField(
        #     model_name='usuario',
        #     name='first_name',
        # ),
        # migrations.RemoveField(
        #     model_name='usuario',
        #     name='groups',
        # ),
        # migrations.RemoveField(
        #     model_name='usuario',
        #     name='is_active',
        # ),
        # migrations.RemoveField(
        #     model_name='usuario',
        #     name='is_staff',
        # ),
        # migrations.RemoveField(
        #     model_name='usuario',
        #     name='is_superuser',
        # ),
        # migrations.RemoveField(
        #     model_name='usuario',
        #     name='last_login',
        # ),
        # migrations.RemoveField(
        #     model_name='usuario',
        #     name='last_name',
        # ),
        # migrations.RemoveField(
        #     model_name='usuario',
        #     name='password',
        # ),
        # migrations.RemoveField(
        #     model_name='usuario',
        #     name='user_permissions',
        # ),
        # migrations.RemoveField(
        #     model_name='usuario',
        #     name='username',
        # ),
    ]
