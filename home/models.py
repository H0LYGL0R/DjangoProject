from django.db import models


class Task(models.Model):
    """Задача ЕГЭ по математике"""
    text = models.TextField(verbose_name="Текст задачи")
    answer = models.FloatField(verbose_name="Правильный ответ")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
        ordering = ['-created_at']

    def __str__(self):
        return f"Задача #{self.id}"