# Generated by Django 5.0.6 on 2025-01-14 10:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ficha', '0003_rename_instrumento_escolhido_assinaturainstrumento_instrumento'),
    ]

    operations = [
        migrations.AddField(
            model_name='assinaturainstrumento',
            name='motivo',
            field=models.CharField(default='Devolução', max_length=100),
        ),
    ]
