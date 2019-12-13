from django.db import models
from users.models import CustomUser
from django.contrib.postgres.fields import JSONField


class Annotation(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.DO_NOTHING)
    data = JSONField(default=dict)

    class Meta:
        db_table = "annotations"
