from django.db import models


class Problem(models.Model):
    """Задача ЕГЭ по математике"""

    class Category(models.TextChoices):
        ALGEBRA = 'algebra', 'Алгебра'
        GEOMETRY = 'geometry', 'Геометрия'
        TRIGONOMETRY = 'trig', 'Тригонометрия'
        CALCULUS = 'calculus', 'Математический анализ'
        STATISTICS = 'stats', 'Теория вероятностей'

    text = models.TextField(verbose_name="Текст задачи")
    answer = models.FloatField(verbose_name="Правильный ответ")
    solution = models.TextField(verbose_name="Решение", blank=True)
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.ALGEBRA,
        verbose_name="Категория"
    )
    ege_number = models.IntegerField(
        verbose_name="Номер в ЕГЭ",
        help_text="Номер задачи в варианте ЕГЭ (1-18)",
        default=1
    )
    difficulty = models.IntegerField(
        verbose_name="Сложность (1-5)",
        choices=[(i, str(i)) for i in range(1, 6)],
        default=3
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Задача ЕГЭ"
        verbose_name_plural = "Задачи ЕГЭ"
        ordering = ['ege_number', 'id']

    def __str__(self):
        return f"Задача {self.ege_number} (#{self.id})"