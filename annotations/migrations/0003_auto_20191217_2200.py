# Generated by Django 2.2.1 on 2019-12-17 22:00

import django.contrib.postgres.indexes
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0002_annotation_updated'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='annotation',
            index=models.Index(fields=['user', 'updated'], name='user_time_idx'),
        ),
        migrations.AddIndex(
            model_name='annotation',
            index=django.contrib.postgres.indexes.GinIndex(fields=['data'], name='data_gin'),
        ),
    ]