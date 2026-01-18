from django.db import models
import random
from django.utils import timezone
from django.contrib.sessions.models import Session


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

    @property
    def stats(self):  # Убедитесь, что здесь stats, а не statistics
        """Общая статистика по этой задаче"""
        stats, created = ProblemStatistics.objects.get_or_create(problem=self)
        return stats

    @staticmethod
    def create_full_variant():
        variant_problems = []
        for number in range(1, 13):
            problems = Problem.objects.filter(ege_number=number)
            if problems.exists():
                variant_problems.append(random.choice(list(problems)))
            else:
                variant_problems.append(Problem(
                    text=f"Задача №{number} (в разработке)",
                    answer=0.0,
                    ege_number=number
                ))
        return variant_problems


class UserStatistics(models.Model):
    """Статистика анонимного пользователя"""
    session_key = models.CharField(
        max_length=40,
        verbose_name="Ключ сессии",
        db_index=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    last_activity = models.DateTimeField(
        auto_now=True,
        verbose_name="Последняя активность"
    )

    # Общая статистика пользователя
    total_attempts = models.IntegerField(
        default=0,
        verbose_name="Всего попыток"
    )
    correct_attempts = models.IntegerField(
        default=0,
        verbose_name="Правильных решений"
    )
    total_score = models.IntegerField(
        default=0,
        verbose_name="Всего баллов"
    )

    # Статистика по типам задач
    problems_by_type = models.JSONField(
        default=dict,
        verbose_name="Статистика по типам задач",
        help_text="Формат: {'1': {'total': 10, 'correct': 8}, ...}"
    )

    class Meta:
        verbose_name = "Статистика пользователя"
        verbose_name_plural = "Статистика пользователей"
        ordering = ['-last_activity']

    def __str__(self):
        return f"Статистика сессии {self.session_key[:10]}..."

    @property
    def accuracy(self):
        """Процент правильных решений"""
        if self.total_attempts == 0:
            return 0
        return round((self.correct_attempts / self.total_attempts) * 100, 1)

    @property
    def average_score(self):
        """Средний балл за задачу"""
        if self.total_attempts == 0:
            return 0
        return round(self.total_score / self.total_attempts, 2)

    @property
    def solved_problems(self):
        """Количество уникальных решенных задач"""
        return UserProblemAttempt.objects.filter(
            session_key=self.session_key,
            is_correct=True
        ).values('problem').distinct().count()

    def update_statistics(self, problem, is_correct, score=1):
        """Обновить статистику после решения задачи"""
        self.total_attempts += 1
        if is_correct:
            self.correct_attempts += 1
            self.total_score += score

        # Обновляем статистику по типу задачи
        problem_type = str(problem.ege_number)
        if problem_type not in self.problems_by_type:
            self.problems_by_type[problem_type] = {
                'total': 0,
                'correct': 0,
                'score': 0
            }

        self.problems_by_type[problem_type]['total'] += 1
        if is_correct:
            self.problems_by_type[problem_type]['correct'] += 1
            self.problems_by_type[problem_type]['score'] += score

        self.save()

    def get_type_statistics(self, ege_number):
        """Получить статистику по конкретному типу задач"""
        stats = self.problems_by_type.get(str(ege_number), {
            'total': 0,
            'correct': 0,
            'score': 0
        })

        accuracy = 0
        if stats['total'] > 0:
            accuracy = round((stats['correct'] / stats['total']) * 100, 1)

        return {
            'total': stats['total'],
            'correct': stats['correct'],
            'score': stats['score'],
            'accuracy': accuracy
        }


class UserProblemAttempt(models.Model):
    """Попытка решения конкретной задачи пользователем"""
    session_key = models.CharField(
        max_length=40,
        verbose_name="Ключ сессии",
        db_index=True
    )
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        verbose_name="Задача"
    )
    is_correct = models.BooleanField(
        verbose_name="Правильно решена"
    )
    user_answer = models.FloatField(
        verbose_name="Ответ пользователя"
    )
    score = models.IntegerField(
        default=0,
        verbose_name="Полученные баллы"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата решения"
    )

    class Meta:
        verbose_name = "Попытка решения"
        verbose_name_plural = "Попытки решений"
        ordering = ['-created_at']

    def __str__(self):
        status = "✓" if self.is_correct else "✗"
        return f"{status} {self.session_key[:8]} - Задача {self.problem.ege_number}"


class ProblemStatistics(models.Model):
    """Общая статистика по задаче"""
    problem = models.OneToOneField(
        Problem,
        on_delete=models.CASCADE,
        related_name='problem_stats',
        verbose_name="Задача"
    )

    # Общая статистика
    total_attempts = models.IntegerField(
        default=0,
        verbose_name="Всего попыток"
    )
    correct_attempts = models.IntegerField(
        default=0,
        verbose_name="Правильных решений"
    )
    total_score = models.IntegerField(
        default=0,
        verbose_name="Всего баллов"
    )

    # Дополнительные метрики
    first_solved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Первый раз решена"
    )
    last_solved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Последний раз решена"
    )

    class Meta:
        verbose_name = "Статистика задачи"
        verbose_name_plural = "Статистика задач"

    def __str__(self):
        return f"Статистика задачи #{self.problem.id}"

    @property
    def accuracy(self):
        """Процент правильных решений"""
        if self.total_attempts == 0:
            return 0
        return round((self.correct_attempts / self.total_attempts) * 100, 1)

    @property
    def average_score(self):
        """Средний балл"""
        if self.total_attempts == 0:
            return 0
        return round(self.total_score / self.total_attempts, 2)

    def update_statistics(self, is_correct, score=1):
        """Обновить статистику задачи"""
        self.total_attempts += 1
        if is_correct:
            self.correct_attempts += 1
            self.total_score += score

            now = timezone.now()
            if not self.first_solved_at:
                self.first_solved_at = now
            self.last_solved_at = now

        self.save()


class GlobalStatistics(models.Model):
    """Глобальная статистика по всем пользователям"""
    total_users = models.IntegerField(
        default=0,
        verbose_name="Всего уникальных пользователей"
    )
    total_attempts = models.IntegerField(
        default=0,
        verbose_name="Всего попыток"
    )
    total_correct_attempts = models.IntegerField(
        default=0,
        verbose_name="Всего правильных решений"
    )
    total_score = models.IntegerField(
        default=0,
        verbose_name="Общая сумма баллов"
    )

    # Статистика по типам задач
    problems_by_type = models.JSONField(
        default=dict,
        verbose_name="Статистика по типам задач",
        help_text="Формат: {'1': {'total': 100, 'correct': 85}, ...}"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Последнее обновление"
    )

    class Meta:
        verbose_name = "Глобальная статистика"
        verbose_name_plural = "Глобальная статистика"

    def __str__(self):
        return f"Глобальная статистика ({self.updated_at.date()})"

    @classmethod
    def get_instance(cls):
        """Получить единственный экземпляр глобальной статистики"""
        instance, created = cls.objects.get_or_create(pk=1)
        return instance

    @property
    def overall_accuracy(self):
        """Общий процент правильных решений"""
        if self.total_attempts == 0:
            return 0
        return round((self.total_correct_attempts / self.total_attempts) * 100, 1)

    @property
    def average_score_per_attempt(self):
        """Средний балл за попытку"""
        if self.total_attempts == 0:
            return 0
        return round(self.total_score / self.total_attempts, 2)

    @property
    def average_score_per_user(self):
        """Средний балл на пользователя"""
        if self.total_users == 0:
            return 0
        return round(self.total_score / self.total_users, 1)

    def update_statistics(self, problem_type, is_correct, score=1):
        """Обновить глобальную статистику"""
        self.total_attempts += 1
        if is_correct:
            self.total_correct_attempts += 1
            self.total_score += score

        # Обновляем статистику по типу задачи
        if str(problem_type) not in self.problems_by_type:
            self.problems_by_type[str(problem_type)] = {
                'total': 0,
                'correct': 0,
                'score': 0
            }

        self.problems_by_type[str(problem_type)]['total'] += 1
        if is_correct:
            self.problems_by_type[str(problem_type)]['correct'] += 1
            self.problems_by_type[str(problem_type)]['score'] += score

        # Обновляем количество уникальных пользователей
        self.total_users = UserStatistics.objects.count()

        self.save()

    def get_type_statistics(self, ege_number):
        """Получить статистику по конкретному типу задач"""
        stats = self.problems_by_type.get(str(ege_number), {
            'total': 0,
            'correct': 0,
            'score': 0
        })

        accuracy = 0
        if stats['total'] > 0:
            accuracy = round((stats['correct'] / stats['total']) * 100, 1)

        average_score = 0
        if stats['total'] > 0:
            average_score = round(stats['score'] / stats['total'], 2)

        return {
            'total': stats['total'],
            'correct': stats['correct'],
            'score': stats['score'],
            'accuracy': accuracy,
            'average_score': average_score
        }