# Generated by Django 4.2.15 on 2024-12-09 08:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cadastro', '0007_remove_infoinstrumento_faixa_nominal_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='pontocalibracao',
            name='descricao',
            field=models.CharField(default=1, max_length=100),
            preserve_default=False,
        ),
    ]