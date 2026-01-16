from django.db import models
import random


class Problem(models.Model):
    text = models.TextField(verbose_name="Текст задачи")
    answer = models.FloatField(verbose_name="Правильный ответ")
    ege_number = models.IntegerField(
        verbose_name="Номер в ЕГЭ",
        choices=[(i, f"Задача {i}") for i in range(1, 19)],
        default=1
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ege_number', 'id']

    def __str__(self):
        return f"Задача {self.ege_number} (#{self.id})"

    @staticmethod
    def get_random_variant():
        """Создать случайный вариант из 3 задач разных номеров"""
        all_numbers = list(range(1, 19))
        selected_numbers = random.sample(all_numbers, min(3, len(all_numbers)))

        variant_problems = []
        for number in selected_numbers:
            problems = Problem.objects.filter(ege_number=number)
            if problems.exists():
                variant_problems.append(random.choice(list(problems)))

        return variant_problems