# Generated by Django 2.2.1 on 2020-01-07 22:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0007_auto_20191219_1032'),
    ]

    operations = [
        migrations.AlterField(
            model_name='annotation',
            name='sessionId',
            field=models.CharField(max_length=48),
        ),
    ]
