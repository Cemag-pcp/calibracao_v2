# Generated by Django 5.0.6 on 2025-01-03 13:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cadastro', '0013_designarinstrumento_pdf_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='pontocalibracao',
            name='status_ponto_calibracao',
            field=models.CharField(choices=[('ativo', 'Ativo'), ('inativo', 'Inativo')], default='ativo', max_length=10),
        ),
    ]