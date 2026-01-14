from django.shortcuts import render
from .models import Problem


def index(request):
    return render(request, 'index.html')


def problem_list(request):
    # Автоматическое создание задач если БД пустая
    if Problem.objects.count() == 0:
        sample_problems = [
            {"text": "Найдите 15% от 80", "answer": 12},
            {"text": "Решите: 2x² - 5x + 3 = 0", "answer": 1.5},
            {"text": "√144", "answer": 12},
            {"text": "2 + 2 × 2", "answer": 6},
            {"text": "sin(30°)", "answer": 0.5},
            {"text": "Площадь круга радиусом 3", "answer": 28.27},
        ]
        for p in sample_problems:
            Problem.objects.create(**p)

    problems = Problem.objects.all()
    return render(request, 'home/problem_list.html', {
        'problems': problems,
        'total': problems.count()
    })