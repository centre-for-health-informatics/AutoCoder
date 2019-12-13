from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    role = models.CharField(db_column='role', max_length=50, choices=[
                            ('coder', 'coder'), ('admin', 'admin')], default='coder')
    verified = models.BooleanField(db_column='verified', default=False)
