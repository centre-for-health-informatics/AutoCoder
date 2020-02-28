from django.db import models

class TreeCode(models.Model):
    code = models.CharField(db_column='code', max_length=20, primary_key=True)
    description = models.CharField(db_column='description', max_length=1000)
    parent = models.CharField(db_column='parent', max_length=20)
    children = models.TextField(db_column='children', max_length=1000)

    class Meta:
        db_table = 'tree_codes'


class Code(models.Model):
    code = models.CharField(db_column='code', max_length=20, primary_key=True)
    description = models.TextField(db_column='description')
    parent = models.CharField(db_column='parent', max_length=20)
    children = models.CharField(db_column='children', max_length=1000)
    times_coded = models.IntegerField(db_column='times_coded', default=0)
    times_coded_dad = models.IntegerField(db_column='times_coded_dad', default=0)
    keyword_terms = models.TextField(db_column='keyword_terms')
    selectable = models.BooleanField(db_column='selectable', default=True)