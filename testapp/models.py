from django.db import models


class Drawing(models.Model):
    name = models.CharField(max_length=32)


class Widget(models.Model):
    name = models.CharField(max_length=32)
    drawing = models.ForeignKey(Drawing)

    quantity = models.PositiveIntegerField()
