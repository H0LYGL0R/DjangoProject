from django.db import models


class Problem(models.Model):
    text = models.TextField()
    answer = models.FloatField()

    def __str__(self):
        return f"Задача {self.id}"