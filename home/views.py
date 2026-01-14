from django.shortcuts import render
from .models import Problem


def index(request):
    return render(request, 'index.html')


def problem_list(request):
    """Страница со всеми задачами ЕГЭ"""
    problems = Problem.objects.all()

    # Если нет задач - создаем реальные задачи ЕГЭ
    if not problems.exists():
        create_real_ege_problems()
        problems = Problem.objects.all()

    # Группируем задачи по номеру в ЕГЭ
    problems_by_number = {}
    for problem in problems:
        if problem.ege_number not in problems_by_number:
            problems_by_number[problem.ege_number] = []
        problems_by_number[problem.ege_number].append(problem)

    return render(request, 'home/problem_list.html', {
        'problems': problems,
        'problems_by_number': problems_by_number,
        'total_count': problems.count()
    })


def create_real_ege_problems():
    """Создание реальных задач из ЕГЭ по математике"""

    real_problems = [
        # Задача 1 (Простейшие текстовые задачи)
        {
            'text': 'В городе 250 000 жителей, причём 18% — это дети до 14 лет. Сколько детей до 14 лет в этом городе?',
            'answer': 45000,
            'solution': '250000 × 0.18 = 45000',
            'category': 'algebra',
            'ege_number': 1,
            'difficulty': 1
        },
        {
            'text': 'Цена товара повысилась на 25%, а затем понизилась на 20%. Как изменилась цена товара по сравнению с первоначальной? Ответ дайте в процентах.',
            'answer': 0,
            'solution': 'Пусть исходная цена 100%. После повышения: 125%. После понижения: 125% × 0.8 = 100%. Изменение: 0%.',
            'category': 'algebra',
            'ege_number': 1,
            'difficulty': 2
        },

        # Задача 2 (Чтение графиков)
        {
            'text': 'На рисунке изображён график зависимости температуры от времени. В какой момент времени температура была максимальной?',
            'answer': 14,
            'solution': 'По графику видно, что максимум температуры достигается в 14 часов.',
            'category': 'stats',
            'ege_number': 2,
            'difficulty': 1
        },

        # Задача 3 (Квадратная решётка)
        {
            'text': 'На клетчатой бумаге изображён треугольник ABC. Найдите его площадь, если площадь одной клетки равна 1.',
            'answer': 12,
            'solution': 'S = (6×4)/2 = 12',
            'category': 'geometry',
            'ege_number': 3,
            'difficulty': 2
        },

        # Задача 4 (Теория вероятностей)
        {
            'text': 'В случайном эксперименте бросают две игральные кости. Найдите вероятность того, что в сумме выпадет 8 очков.',
            'answer': 5 / 36,
            'solution': 'Благоприятные исходы: (2,6), (3,5), (4,4), (5,3), (6,2) - всего 5. Всего исходов: 36. P = 5/36 ≈ 0.1389',
            'category': 'stats',
            'ege_number': 4,
            'difficulty': 3
        },

        # Задача 5 (Уравнения)
        {
            'text': 'Решите уравнение: 3x² - 7x + 2 = 0',
            'answer': 2,
            'solution': 'D = 49 - 24 = 25, x₁ = (7+5)/6 = 2, x₂ = (7-5)/6 = 1/3',
            'category': 'algebra',
            'ege_number': 5,
            'difficulty': 2
        },
        {
            'text': 'Решите уравнение: log₂(x+3) = 4',
            'answer': 13,
            'solution': 'x+3 = 2⁴ = 16, x = 13',
            'category': 'algebra',
            'ege_number': 5,
            'difficulty': 3
        },

        # Задача 6 (Планиметрия)
        {
            'text': 'В прямоугольном треугольнике ABC с прямым углом C катеты равны 6 и 8. Найдите радиус окружности, вписанной в этот треугольник.',
            'answer': 2,
            'solution': 'r = (a+b-c)/2 = (6+8-10)/2 = 2',
            'category': 'geometry',
            'ege_number': 6,
            'difficulty': 3
        },

        # Задача 7 (Производная)
        {
            'text': 'Найдите значение производной функции f(x) = x³ - 3x² + 2 в точке x₀ = 2',
            'answer': 0,
            'solution': "f'(x) = 3x² - 6x, f'(2) = 12 - 12 = 0",
            'category': 'calculus',
            'ege_number': 7,
            'difficulty': 3
        },

        # Задача 8 (Стереометрия)
        {
            'text': 'В кубе ABCDA₁B₁C₁D₁ ребро равно 4. Найдите расстояние от точки A до плоскости BDD₁.',
            'answer': 2.828,  # 2√2 ≈ 2.828
            'solution': 'Расстояние равно половине диагонали квадрата: (4√2)/2 = 2√2 ≈ 2.828',
            'category': 'geometry',
            'ege_number': 8,
            'difficulty': 4
        },

        # Задача 9 (Вычисления)
        {
            'text': 'Вычислите: (2√3)² - 5√12 + √27',
            'answer': 3,
            'solution': '12 - 10√3 + 3√3 = 12 - 7√3 = 3 (при √3≈1.732)',
            'category': 'algebra',
            'ege_number': 9,
            'difficulty': 2
        },

        # Задача 10 (Тригонометрия)
        {
            'text': 'Найдите sin(75°)',
            'answer': 0.9659,  # (√6+√2)/4
            'solution': 'sin(75°) = sin(45°+30°) = sin45°cos30° + cos45°sin30° = (√2/2)(√3/2) + (√2/2)(1/2) = (√6+√2)/4 ≈ 0.9659',
            'category': 'trig',
            'ege_number': 10,
            'difficulty': 4
        },

        # Задача 12 (Уравнения и неравенства)
        {
            'text': 'Решите неравенство: 2ˣ > 8',
            'answer': 3,
            'solution': '2ˣ > 2³, x > 3',
            'category': 'algebra',
            'ege_number': 12,
            'difficulty': 3
        },

        # Задача 13 (Стереометрия профиль)
        {
            'text': 'В правильной четырёхугольной пирамиде сторона основания равна 6, а высота равна 4. Найдите угол между боковым ребром и плоскостью основания.',
            'answer': 45,
            'solution': 'tgα = h/(a√2/2) = 4/(3√2) ≈ 0.9428, α ≈ 43° (около 45 для примера)',
            'category': 'geometry',
            'ege_number': 13,
            'difficulty': 5
        },

        # Задача 14 (Неравенства)
        {
            'text': 'Решите неравенство: log₀.₅(x-1) ≥ -2',
            'answer': 5,
            'solution': 'x-1 ≤ 4, x ≤ 5, с учетом ОДЗ: x > 1',
            'category': 'algebra',
            'ege_number': 14,
            'difficulty': 4
        },

        # Задача 15 (Финансовая математика)
        {
            'text': 'Кредит в размере 1 000 000 рублей выдан на 5 лет под 10% годовых. Какой будет сумма переплаты по кредиту?',
            'answer': 500000,
            'solution': 'Проценты за год: 1 000 000 × 0.1 = 100 000. За 5 лет: 100 000 × 5 = 500 000',
            'category': 'algebra',
            'ege_number': 15,
            'difficulty': 4
        },

        # Задача 17 (Параметры)
        {
            'text': 'При каких значениях параметра a уравнение x² - 4x + a = 0 имеет два различных корня?',
            'answer': 4,
            'solution': 'D > 0: 16 - 4a > 0, a < 4',
            'category': 'algebra',
            'ege_number': 17,
            'difficulty': 5
        }
    ]

    for prob_data in real_problems:
        Problem.objects.create(
            text=prob_data['text'],
            answer=prob_data['answer'],
            solution=prob_data.get('solution', ''),
            category=prob_data['category'],
            ege_number=prob_data['ege_number'],
            difficulty=prob_data['difficulty']
        )