# Generated by Django 4.2.15 on 2024-12-05 10:41

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('inspecao', '0004_alter_envio_laboratorio'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='envio',
            name='analise_certificado',
        ),
        migrations.RemoveField(
            model_name='envio',
            name='data_analise',
        ),
        migrations.RemoveField(
            model_name='envio',
            name='incerteza',
        ),
        migrations.RemoveField(
            model_name='envio',
            name='responsavel_analise',
        ),
        migrations.RemoveField(
            model_name='envio',
            name='tendencia',
        ),
        migrations.CreateModel(
            name='AnaliseCertificado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('analise_certificado', models.CharField(blank=True, choices=[('aprovado', 'Aprovado'), ('reprovado', 'Reprovado')], max_length=20, null=True)),
                ('incerteza', models.FloatField(blank=True, null=True)),
                ('tendencia', models.FloatField(blank=True, null=True)),
                ('data_analise', models.DateField(blank=True, null=True)),
                ('envio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='analise_envio', to='inspecao.envio')),
                ('responsavel_analise', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='responsavel_analise', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
