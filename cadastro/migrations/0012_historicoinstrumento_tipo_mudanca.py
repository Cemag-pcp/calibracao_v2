# Generated by Django 4.2.15 on 2024-12-09 11:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cadastro', '0011_remove_historicoinstrumento_responsavel_anterior_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicoinstrumento',
            name='tipo_mudanca',
            field=models.CharField(choices=[('enviado', 'Enviado'), ('recebido', 'Recebido'), ('analisado', 'Analisado'), ('troca_reponsavel', 'Troca de responsável'), ('primeira_atribuicao', 'Primeira atribuição')], default=1, help_text='Tipo da mudança ocorrida (ex: enviado, recebido, analisado).', max_length=50),
            preserve_default=False,
        ),
    ]