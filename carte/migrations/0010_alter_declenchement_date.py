# Generated by Django 5.0.4 on 2024-04-07 23:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carte', '0009_alter_declenchement_adresse_client_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='declenchement',
            name='DATE',
            field=models.DateField(verbose_name='%d/%m/%Y'),
        ),
    ]