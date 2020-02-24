from django.db import models

class TreeCode(models.Model):
    code = models.CharField(db_column='code', max_length=20, primary_key=True)
    description = models.CharField(db_column='description', max_length=1000)
    parent = models.CharField(db_column='parent', max_length=20)
    children = models.TextField(db_column='children', max_length=1000)

    class Meta:
        db_table = 'tree_codes'