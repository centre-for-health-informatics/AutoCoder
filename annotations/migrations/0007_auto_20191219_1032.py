# Generated by Django 2.2.1 on 2019-12-19 17:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0006_auto_20191218_2239'),
    ]

    operations = [
        migrations.AlterField(
            model_name='annotation',
            name='sessionId',
            field=models.CharField(max_length=48, unique=True),
        ),
    ]