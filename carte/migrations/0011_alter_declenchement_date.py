# Generated by Django 5.0.4 on 2024-04-08 11:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carte', '0010_alter_declenchement_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='declenchement',
            name='DATE',
            field=models.CharField(max_length=10),
        ),
    ]
