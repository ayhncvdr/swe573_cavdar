# Generated by Django 4.1.7 on 2023-05-24 11:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_alter_profile_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='id_user',
        ),
    ]
