# Generated manually to add missing fields

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_venta_ciudad_venta_paypal_payer_id_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='venta',
            name='aceptada_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ventas_aceptadas', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='venta',
            name='fecha_aceptacion',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ] 