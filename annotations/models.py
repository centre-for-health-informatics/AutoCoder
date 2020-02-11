from django.db import models
from users.models import CustomUser
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex


class Annotation(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.DO_NOTHING)
    sessionId = models.CharField(null=False, max_length=48, unique=False, blank=False)
    data = JSONField(default=dict)
    updated = models.DateTimeField(auto_now=True, editable=False, null=False, blank=False)

    class Meta:
        db_table = "annotations"

        indexes = [

            GinIndex(
                fields=['user', 'data', 'updated', 'sessionId'],
                name='annotation_gin'
            )
        ]

class TreeCode(models.Model):
    code = models.CharField(db_column='code', max_length=20, primary_key=True)
    description = models.CharField(db_column='description', max_length=1000)
    parent = models.CharField(db_column='parent', max_length=20)
    children = models.TextField(db_column='children', max_length=1000)

    class Meta:
        db_table = 'tree_codes'