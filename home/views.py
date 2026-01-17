from django.shortcuts import render, get_object_or_404, redirect
from .models import Problem
import random
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


def index(request):
    return render(request, 'index.html')


def choose_mode(request):
    return render(request, 'home/choose.html')


def full_variant(request):
    """
    Отображение полного варианта из 12 задач (по одной на номер 1–12)
    """
    variant_id = request.GET.get('variant_id', 1)

    # Получаем по одной задаче для каждого номера от 1 до 12
    selected_problems = []
    for number in range(1, 13):  # от 1 до 12 включительно
        problems_for_number = Problem.objects.filter(ege_number=number)
        if problems_for_number.exists():
            # Выбираем случайную задачу для этого номера
            problem = random.choice(problems_for_number)
            selected_problems.append(problem)

    # Сортируем задачи по ege_number, чтобы гарантировать порядок
    selected_problems.sort(key=lambda x: x.ege_number)

    # Сохраняем ID задач в сессии, чтобы потом использовать в check_variant
    request.session['current_variant_ids'] = [p.id for p in selected_problems]
    request.session['variant_id'] = variant_id

    return render(request, 'home/full_variant.html', {
        'problems': selected_problems,
        'variant_id': variant_id,
    })

def check_variant(request):
    """
    Проверка текущего варианта и перенаправление на страницу с результатами
    """
    if request.method != 'POST':
        return redirect('full_variant')

    # Получаем ID задач из сессии
    problem_ids = request.session.get('current_variant_ids', [])
    if not problem_ids:
        return redirect('full_variant')

    # Получаем задачи в том же порядке
    selected_problems = list(Problem.objects.filter(id__in=problem_ids))
    selected_problems.sort(key=lambda x: problem_ids.index(x.id))

    results = []
    total_score = 0

    for problem in selected_problems:
        user_answer_str = request.POST.get(f'answer_{problem.id}', '').strip()
        if not user_answer_str:
            results.append({
                'problem_id': problem.id,
                'problem_number': problem.ege_number,
                'is_correct': False,
                'correct_answer': problem.answer,
                'user_answer': '',
                'score': 0
            })
            continue

        try:
            user_answer = float(user_answer_str)
            correct_answer = float(problem.answer)
            if abs(user_answer - correct_answer) < 0.01:
                is_correct = True
                score = 1
                total_score += score
            else:
                is_correct = False
                score = 0
        except ValueError:
            is_correct = False
            score = 0

        results.append({
            'problem_id': problem.id,
            'problem_number': problem.ege_number,
            'is_correct': is_correct,
            'correct_answer': problem.answer,
            'user_answer': user_answer_str,
            'score': score
        })

    # Сохраняем результаты в сессии и перенаправляем на страницу с результатами
    request.session['check_results'] = results
    request.session['total_score'] = total_score
    request.session['max_score'] = len(selected_problems)

    return redirect('show_result')

def show_result(request):
    """
    Отображение результатов проверки
    """
    results = request.session.get('check_results', [])
    total_score = request.session.get('total_score', 0)
    max_score = request.session.get('max_score', 0)

    if not results:
        return redirect('full_variant')

    return render(request, 'home/result.html', {
        'results': results,
        'total_score': total_score,
        'max_score': max_score,
    })

def problems_by_number(request, ege_number):
    problems = Problem.objects.filter(ege_number=ege_number)
    return render(request, 'home/problems_by_number.html', {
        'problems': problems,
        'ege_number': ege_number,
        'total': problems.count()
    })

def all_numbers(request):
    numbers = []
    for i in range(1, 13):  # Только от 1 до 12
        count = Problem.objects.filter(ege_number=i).count()
        numbers.append({
            'number': i,
            'count': count
        })
    return render(request, 'home/all_numbers.html', {'numbers': numbers})

