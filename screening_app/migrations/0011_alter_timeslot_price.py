# Generated by Django 3.2 on 2021-06-12 03:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('screening_app', '0010_auto_20210508_2040'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timeslot',
            name='price',
            field=models.FloatField(default=2.0),
        ),
    ]
