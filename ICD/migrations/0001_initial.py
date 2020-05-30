# Generated by Django 2.2.1 on 2020-02-14 16:53

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TreeCode',
            fields=[
                ('code', models.CharField(db_column='code', max_length=20, primary_key=True, serialize=False)),
                ('description', models.CharField(db_column='description', max_length=1000)),
                ('parent', models.CharField(db_column='parent', max_length=20)),
                ('children', models.TextField(db_column='children', max_length=1000)),
            ],
            options={
                'db_table': 'tree_codes',
            },
        ),
    ]