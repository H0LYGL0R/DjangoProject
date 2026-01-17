from django.db import models
import random
from django.utils import timezone


class Problem(models.Model):
    text = models.TextField(verbose_name="Текст задачи")
    answer = models.FloatField(verbose_name="Правильный ответ")
    ege_number = models.IntegerField(
        verbose_name="Номер в ЕГЭ",
        choices=[(i, f"Задача {i}") for i in range(1, 13)],
        default=1
    )

    class Meta:
        ordering = ['ege_number', 'id']

    def __str__(self):
        return f"Задача {self.ege_number} (#{self.id})"

    @staticmethod
    def create_full_variant():
        variant_problems = []
        for number in range(1, 13):
            problems = Problem.objects.filter(ege_number=number)
            if problems.exists():
                variant_problems.append(random.choice(list(problems)))
            else:
                # Если нет задачи этого типа, создаем заглушку
                variant_problems.append(Problem(
                    text=f"Задача №{number} (в разработке)",
                    answer=0.0,
                    ege_number=number
                ))
        return variant_problems