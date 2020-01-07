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
