# Generated by Django 5.0.6 on 2025-02-05 14:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cadastro', '0017_alter_historicoinstrumento_tipo_mudanca'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicoinstrumento',
            name='tipo_mudanca',
            field=models.CharField(choices=[('enviado', 'Enviado'), ('recebido', 'Recebido'), ('analisado', 'Analisado'), ('troca_reponsavel', 'Troca de responsável'), ('atribuicao', 'Atribuição'), ('danificado', 'Danificado'), ('devolvido', 'Devolvido')], help_text='Tipo da mudança ocorrida (ex: enviado, recebido, analisado).', max_length=50),
        ),
    ]
