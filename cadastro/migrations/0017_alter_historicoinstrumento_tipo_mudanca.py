# Generated by Django 5.0.6 on 2025-02-04 14:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cadastro', '0016_delete_assinaturainstrumento'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicoinstrumento',
            name='tipo_mudanca',
            field=models.CharField(choices=[('enviado', 'Enviado'), ('recebido', 'Recebido'), ('analisado', 'Analisado'), ('troca_reponsavel', 'Troca de responsável'), ('primeira_atribuicao', 'Primeira atribuição'), ('danificado', 'Danificado')], help_text='Tipo da mudança ocorrida (ex: enviado, recebido, analisado).', max_length=50),
        ),
    ]
