# Generated by Django 4.2.15 on 2024-12-06 11:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inspecao', '0008_alter_envio_pdf'),
    ]

    operations = [
        migrations.AddField(
            model_name='envio',
            name='analise',
            field=models.BooleanField(default=False, null=True),
        ),
    ]
