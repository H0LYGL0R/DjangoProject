from django.shortcuts import render, get_object_or_404, redirect
from .models import Problem, UserStatistics, UserProblemAttempt
import random
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone
from django.db.models import Count, Sum, Avg, F, FloatField, Q


def get_or_create_user_statistics(request):
    """Получить или создать статистику пользователя по сессии"""
    session_key = request.session.session_key
    if not session_key:
        request.session.save()
        session_key = request.session.session_key

    stats, created = UserStatistics.objects.get_or_create(
        session_key=session_key
    )
    return stats


def get_global_statistics():
    """Получить глобальную статистику через агрегацию"""
    # Общая статистика
    total_users = UserStatistics.objects.count()

    # Получаем агрегированные данные за один запрос
    attempts_stats = UserProblemAttempt.objects.aggregate(
        total_attempts=Count('id'),
        total_correct_attempts=Count('id', filter=Q(is_correct=True)),
        total_score=Sum('score')
    )

    total_attempts = attempts_stats['total_attempts'] or 0
    total_correct_attempts = attempts_stats['total_correct_attempts'] or 0
    total_score = attempts_stats['total_score'] or 0

    # Точность
    overall_accuracy = 0
    if total_attempts > 0:
        overall_accuracy = round((total_correct_attempts / total_attempts) * 100, 1)

    # Средний балл
    average_score_per_attempt = 0
    if total_attempts > 0:
        average_score_per_attempt = round(total_score / total_attempts, 2)

    # Средний балл на пользователя
    average_score_per_user = 0
    if total_users > 0:
        average_score_per_user = round(total_score / total_users, 1)

    # Статистика по типам задач
    problems_by_type = {}
    for i in range(1, 13):
        # Используем агрегацию за один запрос
        type_stats = UserProblemAttempt.objects.filter(
            problem__ege_number=i
        ).aggregate(
            total=Count('id'),
            correct=Count('id', filter=Q(is_correct=True)),
            total_score=Sum('score')
        )

        total = type_stats['total'] or 0
        correct = type_stats['correct'] or 0
        score = type_stats['total_score'] or 0

        accuracy = 0
        if total > 0:
            accuracy = round((correct / total) * 100, 1)

        avg_score = 0
        if total > 0:
            avg_score = round(score / total, 2)

        problems_by_type[str(i)] = {
            'total': total,
            'correct': correct,
            'score': score,
            'accuracy': accuracy,
            'average_score': avg_score
        }

    return {
        'total_users': total_users,
        'total_attempts': total_attempts,
        'total_correct_attempts': total_correct_attempts,
        'total_score': total_score,
        'overall_accuracy': overall_accuracy,
        'average_score_per_attempt': average_score_per_attempt,
        'average_score_per_user': average_score_per_user,
        'problems_by_type': problems_by_type,
        'updated_at': timezone.now()
    }


def index(request):
    try:
        # Получаем глобальную статистику
        global_stats = get_global_statistics()
    except Exception as e:
        # Если произошла ошибка (например, таблицы еще не созданы)
        global_stats = {
            'total_users': 0,
            'total_attempts': 0,
            'total_correct_attempts': 0,
            'total_score': 0,
            'overall_accuracy': 0,
            'average_score_per_attempt': 0,
            'average_score_per_user': 0,
            'problems_by_type': {},
            'updated_at': timezone.now()
        }

    # Получаем последние успешные решения
    recent_successes = UserProblemAttempt.objects.filter(
        is_correct=True
    ).select_related('problem').order_by('-created_at')[:10]

    # Самые сложные задачи (по проценту правильных решений)
    # Получаем задачи с попытками
    problems_with_attempts = []
    problems = Problem.objects.all()

    for problem in problems:
        stats = problem.stats
        if stats['total_attempts'] > 0:
            problems_with_attempts.append({
                'problem': problem,
                'stats': stats,
                'accuracy': stats['accuracy']
            })

    # Сортируем по точности (от меньшей к большей) и берем топ-5
    difficult_problems = sorted(problems_with_attempts, key=lambda x: x['accuracy'])[:5]

    return render(request, 'index.html', {
        'global_stats': global_stats,
        'recent_successes': recent_successes,
        'difficult_problems': difficult_problems,
    })


def choose_mode(request):
    # Получаем статистику пользователя
    user_stats = get_or_create_user_statistics(request)

    return render(request, 'home/choose.html', {
        'user_stats': user_stats,
    })


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

    # Получаем статистику пользователя
    user_stats = get_or_create_user_statistics(request)

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
            # Сохраняем попытку (неверный ответ)
            UserProblemAttempt.objects.create(
                session_key=request.session.session_key,
                problem=problem,
                is_correct=False,
                user_answer=0,
                score=0
            )
            # Обновляем статистику пользователя
            user_stats.update_statistics(problem, False, 0)
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

        # Сохраняем попытку
        UserProblemAttempt.objects.create(
            session_key=request.session.session_key,
            problem=problem,
            is_correct=is_correct,
            user_answer=user_answer if 'user_answer' in locals() else 0,
            score=score
        )

        # Обновляем статистику пользователя
        user_stats.update_statistics(problem, is_correct, score)

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

    # Получаем статистику пользователя и глобальную статистику
    user_stats = get_or_create_user_statistics(request)
    global_stats = get_global_statistics()

    # Получаем статистику по типам задач из результатов
    type_stats = {}
    for result in results:
        problem_type = result['problem_number']
        type_stats[problem_type] = global_stats['problems_by_type'].get(str(problem_type), {
            'total': 0,
            'correct': 0,
            'score': 0,
            'accuracy': 0,
            'average_score': 0
        })

    # Вычисляем процент выполнения
    percentage = 0
    if max_score > 0:
        percentage = round((total_score / max_score) * 100, 2)

    return render(request, 'home/result.html', {
        'results': results,
        'total_score': total_score,
        'max_score': max_score,
        'percentage': percentage,
        'user_stats': user_stats,
        'global_stats': global_stats,
        'type_stats': type_stats,
    })


def problems_by_number(request, ege_number):
    problems = Problem.objects.filter(ege_number=ege_number)

    # Получаем статистику пользователя по этому типу задач
    user_stats = get_or_create_user_statistics(request)
    user_type_stats = user_stats.get_type_statistics(ege_number)

    # Получаем глобальную статистику по этому типу задач
    global_stats = get_global_statistics()
    global_type_stats = global_stats['problems_by_type'].get(str(ege_number), {
        'total': 0,
        'correct': 0,
        'score': 0,
        'accuracy': 0,
        'average_score': 0
    })

    # Получаем общую статистику по всем задачам этого типа
    problems_with_stats = []
    for problem in problems:
        stats = problem.stats
        problems_with_stats.append({
            'problem': problem,
            'stats': stats
        })

    return render(request, 'home/problems_by_number.html', {
        'problems': problems,
        'problems_with_stats': problems_with_stats,
        'ege_number': ege_number,
        'total': problems.count(),
        'user_type_stats': user_type_stats,
        'global_type_stats': global_type_stats,
    })


def all_numbers(request):
    numbers = []
    global_stats = get_global_statistics()

    for i in range(1, 13):  # Только от 1 до 12
        count = Problem.objects.filter(ege_number=i).count()
        type_stats = global_stats['problems_by_type'].get(str(i), {
            'total': 0,
            'correct': 0,
            'accuracy': 0
        })
        numbers.append({
            'number': i,
            'count': count,
            'total_attempts': type_stats['total'],
            'accuracy': type_stats['accuracy']
        })

    # Получаем статистику пользователя
    user_stats = get_or_create_user_statistics(request)

    return render(request, 'home/all_numbers.html', {
        'numbers': numbers,
        'user_stats': user_stats,
    })


def user_statistics(request):
    """Страница статистики пользователя"""
    user_stats = get_or_create_user_statistics(request)
    global_stats = get_global_statistics()

    # Получаем последние попытки пользователя
    recent_attempts = UserProblemAttempt.objects.filter(
        session_key=request.session.session_key
    ).select_related('problem').order_by('-created_at')[:20]

    # Получаем статистику по всем типам задач
    type_stats = []
    for i in range(1, 13):
        user_type = user_stats.get_type_statistics(i)
        global_type = global_stats['problems_by_type'].get(str(i), {
            'total': 0,
            'correct': 0,
            'score': 0,
            'accuracy': 0,
            'average_score': 0
        })

        type_stats.append({
            'number': i,
            'user': user_type,
            'global': global_type
        })

    # Самые сложные задачи для пользователя
    user_attempts_by_problem = UserProblemAttempt.objects.filter(
        session_key=request.session.session_key
    ).values('problem').annotate(
        total=Count('id'),
        correct=Count('id', filter=Q(is_correct=True))
    )

    # Преобразуем в список для дальнейшей обработки
    difficult_problems_data = []
    for attempt in user_attempts_by_problem:
        if attempt['total'] > 0:
            problem = Problem.objects.get(id=attempt['problem'])
            accuracy = 0
            if attempt['total'] > 0:
                accuracy = (attempt['correct'] / attempt['total']) * 100
            difficult_problems_data.append({
                'problem': problem,
                'total': attempt['total'],
                'correct': attempt['correct'],
                'accuracy': round(accuracy, 1)
            })

    # Сортируем по точности (от меньшей к большей)
    difficult_problems = sorted(difficult_problems_data, key=lambda x: x['accuracy'])[:5]

    return render(request, 'home/user_statistics.html', {
        'user_stats': user_stats,
        'global_stats': global_stats,
        'recent_attempts': recent_attempts,
        'type_stats': type_stats,
        'difficult_problems': difficult_problems,
    })


def global_statistics(request):
    """Страница глобальной статистики"""
    global_stats = get_global_statistics()

    # Топ самых сложных задач
    # Получаем статистику по всем задачам
    problem_stats = []
    problems = Problem.objects.all()
    for problem in problems:
        stats = problem.stats
        if stats['total_attempts'] >= 5:  # Минимум 5 попыток для включения в рейтинг
            problem_stats.append({
                'problem': problem,
                'stats': stats,
                'accuracy': stats['accuracy']
            })

    # Сортируем по точности (от меньшей к большей) - самые сложные
    difficult_problems = sorted(problem_stats, key=lambda x: x['accuracy'])[:10]

    # Топ самых легких задач
    easy_problems = sorted(problem_stats, key=lambda x: x['accuracy'], reverse=True)[:10]

    # Самые активные пользователи (по количеству попыток)
    active_users = UserStatistics.objects.filter(
        total_attempts__gt=0
    ).order_by('-total_attempts')[:10]

    # Последние успешные решения
    recent_successes = UserProblemAttempt.objects.filter(
        is_correct=True
    ).select_related('problem').order_by('-created_at')[:10]

    # Статистика по типам задач
    type_stats = []
    for i in range(1, 13):
        stats = global_stats['problems_by_type'].get(str(i), {
            'total': 0,
            'correct': 0,
            'score': 0,
            'accuracy': 0,
            'average_score': 0
        })
        type_stats.append({
            'number': i,
            'stats': stats
        })

    return render(request, 'home/global_statistics.html', {
        'global_stats': global_stats,
        'difficult_problems': difficult_problems,
        'easy_problems': easy_problems,
        'active_users': active_users,
        'recent_successes': recent_successes,
        'type_stats': type_stats,
    })

