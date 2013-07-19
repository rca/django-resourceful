from django.db import models


class Widget(models.Model):
    name = models.CharField(max_length=32)
    quantity = models.PositiveIntegerField()
