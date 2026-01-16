from django.shortcuts import render, get_object_or_404
from .models import Problem
import random
from django.http import JsonResponse


def index(request):
    return render(request, 'index.html')


def choose_mode(request):
    """Страница выбора режима"""
    return render(request, 'home/choose.html')


def full_variant(request):
    """Полный вариант ЕГЭ (задачи 1-18)"""
    variant_problems = Problem.create_full_variant()

    # Если в БД нет задач, создаем тестовые
    if Problem.objects.count() == 0:
        create_sample_problems()
        variant_problems = Problem.create_full_variant()

    return render(request, 'home/full_variant.html', {
        'problems': variant_problems,
        'variant_id': random.randint(1000, 9999),
        'total_tasks': 18
    })


def check_variant(request):
    """Проверка всего варианта (AJAX)"""
    if request.method == 'POST':
        results = []
        total_score = 0

        for key, value in request.POST.items():
            if key.startswith('answer_'):
                problem_id = int(key.split('_')[1])
                user_answer = value.strip()

                try:
                    problem = Problem.objects.get(id=problem_id)
                    user_float = float(user_answer) if user_answer else None

                    if user_float is not None and abs(user_float - problem.answer) < 0.01:
                        is_correct = True
                        score = 1
                        total_score += score
                    else:
                        is_correct = False
                        score = 0

                    results.append({
                        'problem_id': problem_id,
                        'is_correct': is_correct,
                        'correct_answer': problem.answer,
                        'user_answer': user_answer,
                        'score': score
                    })
                except (Problem.DoesNotExist, ValueError):
                    continue

        return JsonResponse({
            'results': results,
            'total_score': total_score,
            'max_score': len(results)
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)


def problems_by_number(request, ege_number):
    """Все задачи определенного номера"""
    problems = Problem.objects.filter(ege_number=ege_number)
    return render(request, 'home/problems_by_number.html', {
        'problems': problems,
        'ege_number': ege_number,
        'total': problems.count()
    })


def all_numbers(request):
    """Страница со всеми номерами"""
    numbers = []
    for i in range(1, 19):
        count = Problem.objects.filter(ege_number=i).count()
        numbers.append({
            'number': i,
            'count': count
        })
    return render(request, 'home/all_numbers.html', {'numbers': numbers})


def create_sample_problems():
    """Создание тестовых задач для всех номеров"""
    if Problem.objects.count() > 0:
        return

    sample_texts = {
        1: "Найдите 15% от числа 80",
        2: "На графике показана температура воздуха. Найдите разницу между максимальной и минимальной температурой",
        3: "На клетчатой бумаге изображен треугольник. Найдите его площадь, если площадь одной клетки равна 1",
        4: "В случайном эксперименте бросают игральную кость. Найдите вероятность того, что выпадет четное число",
        5: "Решите уравнение: 2x² - 5x + 3 = 0",
        6: "В прямоугольном треугольнике катеты равны 6 и 8. Найдите гипотенузу",
        7: "Найдите производную функции f(x) = x³ - 3x² в точке x = 2",
        8: "В кубе ABCDA₁B₁C₁D₁ ребро равно 4. Найдите расстояние между прямыми AB и C₁D₁",
        9: "Вычислите: (3√2)² - √50 + √8",
        10: "Найдите значение выражения: sin²(30°) + cos²(30°)",
        11: "Найдите наибольшее значение функции f(x) = -x² + 4x + 3 на отрезке [0, 5]",
        12: "Решите уравнение: 2ˣ = 8",
        13: "В правильной четырехугольной пирамиде сторона основания равна 6, высота равна 4. Найдите объем пирамиды",
        14: "Решите неравенство: log₀.₅(x-1) ≥ -2",
        15: "Кредит в размере 1000000 рублей выдан на 5 лет под 10% годовых. Найдите сумму переплаты",
        16: "В треугольнике ABC угол C равен 90°, AC = 6, BC = 8. Найдите радиус описанной окружности",
        17: "При каких значениях параметра a уравнение x² + 2x + a = 0 имеет два различных корня?",
        18: "Сумма двух натуральных чисел равна 15, а их произведение равно 56. Найдите эти числа"
    }

    sample_answers = {
        1: 12, 2: 10, 3: 12, 4: 0.5, 5: 1.5, 6: 10, 7: 0, 8: 4,
        9: 18, 10: 1, 11: 7, 12: 3, 13: 48, 14: 5, 15: 500000,
        16: 5, 17: 1, 18: 7
    }

    for ege_number in range(1, 19):
        Problem.objects.create(
            text=sample_texts.get(ege_number, f"Задача №{ege_number}"),
            answer=sample_answers.get(ege_number, ege_number),
            ege_number=ege_number
        )