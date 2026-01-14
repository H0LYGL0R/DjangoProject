from django.db import models


class Task(models.Model):
    text = models.TextField()
    answer = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
