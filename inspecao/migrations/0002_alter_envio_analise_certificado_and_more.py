# Generated by Django 4.2.15 on 2024-09-02 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inspecao', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='envio',
            name='analise_certificado',
            field=models.CharField(blank=True, choices=[('aprovado', 'Aprovado'), ('reprovado', 'Reprovado')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='envio',
            name='data_analise',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='envio',
            name='incerteza',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='envio',
            name='tendencia',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
