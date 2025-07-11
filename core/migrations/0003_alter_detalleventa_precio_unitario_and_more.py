# Generated by Django 5.2.1 on 2025-06-02 22:14

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_empleado_debe_cambiar_password'),
    ]

    operations = [
        migrations.AlterField(
            model_name='detalleventa',
            name='precio_unitario',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='detalleventa',
            name='subtotal',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='empleado',
            name='comision',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='producto',
            name='categoria',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.categoria'),
        ),
        migrations.AlterField(
            model_name='producto',
            name='imagen',
            field=models.ImageField(blank=True, null=True, upload_to='productos/'),
        ),
        migrations.AlterField(
            model_name='producto',
            name='precio',
            field=models.IntegerField(validators=[django.core.validators.MinValueValidator(0, message='El precio no puede ser negativo')]),
        ),
        migrations.AlterField(
            model_name='producto',
            name='precio_anterior',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='producto',
            name='stock',
            field=models.IntegerField(validators=[django.core.validators.MinValueValidator(0, message='El stock no puede ser negativo')]),
        ),
        migrations.AlterField(
            model_name='venta',
            name='total',
            field=models.IntegerField(),
        ),
    ]
