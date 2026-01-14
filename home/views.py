from django.shortcuts import render
from .models import Task


def index(request):
    return render(request, 'index.html')


def task_list(request):
    tasks = Task.objects.all()

    # Если нет задач - создаем тестовые
    if not tasks.exists():
        create_sample_tasks()
        tasks = Task.objects.all()

    return render(request, 'task_list.html', {'tasks': tasks})


def create_sample_tasks():
    """Создание тестовых задач ЕГЭ"""
    sample_tasks = [
        {
            'text': 'В городе 200000 жителей, причём 30% — это пенсионеры. Сколько пенсионеров в этом городе?',
            'answer': 60000
        },
        {
            'text': 'Решите уравнение: 2x² - 5x + 3 = 0',
            'answer': 1.5  # или 1 (оба корня, но в ЕГЭ часто один ответ)
        },
        {
            'text': 'Найдите производную функции f(x) = 3x² + 2x - 5 в точке x = 2',
            'answer': 14
        },
        {
            'text': 'В прямоугольном треугольнике катеты равны 6 и 8. Найдите гипотенузу.',
            'answer': 10
        },
        {
            'text': 'Сколько будет 15% от 80?',
            'answer': 12
        },
        {
            'text': 'Найдите значение выражения: log₂(16)',
            'answer': 4
        },
        {
            'text': 'Решите неравенство: 3x - 7 > 5',
            'answer': 4  # x > 4
        },
        {
            'text': 'Площадь круга равна 25π. Найдите его радиус.',
            'answer': 5
        },
        {
            'text': 'Найдите sin(30°)',
            'answer': 0.5
        },
        {
            'text': 'Сумма двух чисел равна 15, а их произведение равно 56. Найдите эти числа.',
            'answer': 7  # или 8 (пары 7 и 8)
        },
    ]

    for task_data in sample_tasks:
        Task.objects.create(
            text=task_data['text'],
            answer=task_data['answer']
        )