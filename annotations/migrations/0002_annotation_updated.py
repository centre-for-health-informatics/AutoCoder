# Generated by Django 2.2.1 on 2019-12-16 04:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='annotation',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
