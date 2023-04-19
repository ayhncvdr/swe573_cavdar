# Generated by Django 4.1.7 on 2023-04-19 13:02

import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_alter_location_area'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='area',
            field=django.contrib.gis.db.models.fields.PolygonField(blank=True, geography=True, null=True, srid=4326),
        ),
    ]
