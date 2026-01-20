from django.shortcuts import render, get_object_or_404, redirect
from .models import Problem, UserStatistics, UserProblemAttempt
import random
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone
from django.db.models import Count, Sum, Avg, F, FloatField, Q
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import io
import base64
import numpy as np
from datetime import timedelta


def get_or_create_user_statistics(request):
    session_key = request.session.session_key
    if not session_key:
        request.session.save()
        session_key = request.session.session_key

    stats, created = UserStatistics.objects.get_or_create(
        session_key=session_key
    )
    return stats


def get_global_statistics():
    total_users = UserStatistics.objects.count()

    attempts_stats = UserProblemAttempt.objects.aggregate(
        total_attempts=Count('id'),
        total_correct_attempts=Count('id', filter=Q(is_correct=True)),
        total_score=Sum('score')
    )

    total_attempts = attempts_stats['total_attempts'] or 0
    total_correct_attempts = attempts_stats['total_correct_attempts'] or 0
    total_score = attempts_stats['total_score'] or 0

    overall_accuracy = 0
    if total_attempts > 0:
        overall_accuracy = round((total_correct_attempts / total_attempts) * 100, 1)

    average_score_per_attempt = 0
    if total_attempts > 0:
        average_score_per_attempt = round(total_score / total_attempts, 2)

    average_score_per_user = 0
    if total_users > 0:
        average_score_per_user = round(total_score / total_users, 1)

    problems_by_type = {}
    for i in range(1, 13):
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
        global_stats = get_global_statistics()
    except Exception as e:
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

    recent_successes = UserProblemAttempt.objects.filter(
        is_correct=True
    ).select_related('problem').order_by('-created_at')[:10]

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

    difficult_problems = sorted(problems_with_attempts, key=lambda x: x['accuracy'])[:5]

    return render(request, 'home/index.html', {
        'global_stats': global_stats,
        'recent_successes': recent_successes,
        'difficult_problems': difficult_problems,
    })


def choose_mode(request):
    user_stats = get_or_create_user_statistics(request)
    return render(request, 'home/choose.html', {
        'user_stats': user_stats,
    })


def full_variant(request):
    variant_id = request.GET.get('variant_id', 1)

    selected_problems = []
    for number in range(1, 13):
        problems_for_number = Problem.objects.filter(ege_number=number)
        if problems_for_number.exists():
            problem = random.choice(problems_for_number)
            selected_problems.append(problem)

    selected_problems.sort(key=lambda x: x.ege_number)

    request.session['current_variant_ids'] = [p.id for p in selected_problems]
    request.session['variant_id'] = variant_id

    return render(request, 'home/full_variant.html', {
        'problems': selected_problems,
        'variant_id': variant_id,
    })


def check_variant(request):
    if request.method != 'POST':
        return redirect('full_variant')

    problem_ids = request.session.get('current_variant_ids', [])
    if not problem_ids:
        return redirect('full_variant')

    selected_problems = list(Problem.objects.filter(id__in=problem_ids))
    selected_problems.sort(key=lambda x: problem_ids.index(x.id))

    results = []
    total_score = 0

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
            UserProblemAttempt.objects.create(
                session_key=request.session.session_key,
                problem=problem,
                is_correct=False,
                user_answer=0,
                score=0
            )
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

        UserProblemAttempt.objects.create(
            session_key=request.session.session_key,
            problem=problem,
            is_correct=is_correct,
            user_answer=user_answer if 'user_answer' in locals() else 0,
            score=score
        )

        user_stats.update_statistics(problem, is_correct, score)

    request.session['check_results'] = results
    request.session['total_score'] = total_score
    request.session['max_score'] = len(selected_problems)

    return redirect('show_result')


def show_result(request):
    results = request.session.get('check_results', [])
    total_score = request.session.get('total_score', 0)
    max_score = request.session.get('max_score', 0)

    if not results:
        return redirect('full_variant')

    user_stats = get_or_create_user_statistics(request)
    global_stats = get_global_statistics()

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

    user_stats = get_or_create_user_statistics(request)
    user_type_stats = user_stats.get_type_statistics(ege_number)

    global_stats = get_global_statistics()
    global_type_stats = global_stats['problems_by_type'].get(str(ege_number), {
        'total': 0,
        'correct': 0,
        'score': 0,
        'accuracy': 0,
        'average_score': 0
    })

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

    for i in range(1, 13):
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

    user_stats = get_or_create_user_statistics(request)

    return render(request, 'home/all_numbers.html', {
        'numbers': numbers,
        'user_stats': user_stats,
    })


def generate_progress_chart(request):
    try:
        user_stats = get_or_create_user_statistics(request)

        user_attempts = UserProblemAttempt.objects.filter(
            session_key=request.session.session_key
        ).order_by('created_at')

        if user_attempts.count() <= 1:
            return None

        attempt_numbers = []
        cumulative_accuracy = []
        correct_count = 0

        for i, attempt in enumerate(user_attempts, 1):
            if attempt.is_correct:
                correct_count += 1
            current_accuracy = (correct_count / i) * 100
            attempt_numbers.append(i)
            cumulative_accuracy.append(current_accuracy)

        plt.figure(figsize=(12, 6))

        plt.plot(attempt_numbers, cumulative_accuracy,
                 color='#4CAF50', linewidth=3, marker='o', markersize=5,
                 label='Точность (%)')

        plt.fill_between(attempt_numbers, cumulative_accuracy, alpha=0.2, color='#4CAF50')

        avg_accuracy = user_stats.accuracy
        plt.axhline(y=avg_accuracy, color='#FF5722', linestyle='--',
                    linewidth=2, alpha=0.7, label=f'Средняя: {avg_accuracy:.1f}%')

        plt.xlabel('Номер попытки', fontsize=12, fontweight='bold')
        plt.ylabel('Точность (%)', fontsize=12, fontweight='bold')
        plt.title('Динамика точности решений', fontsize=16, fontweight='bold', pad=20)
        plt.grid(True, alpha=0.3, linestyle='--')
        plt.legend(loc='best')
        plt.ylim(0, 100)

        if len(cumulative_accuracy) > 0:
            last_acc = cumulative_accuracy[-1]
            plt.annotate(f'{last_acc:.1f}%',
                         xy=(attempt_numbers[-1], last_acc),
                         xytext=(10, 10), textcoords='offset points',
                         bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                         arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

        plt.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()

        return base64.b64encode(image_png).decode('utf-8')

    except Exception as e:
        print(f"Ошибка при генерации графика прогресса: {e}")
        return None


def generate_global_accuracy_chart():
    try:
        global_stats = get_global_statistics()

        problem_numbers = list(range(1, 13))
        accuracies = []

        for i in problem_numbers:
            stats = global_stats['problems_by_type'].get(str(i), {'accuracy': 0})
            accuracies.append(stats['accuracy'])

        plt.figure(figsize=(14, 7))

        colors = []
        for acc in accuracies:
            if acc >= 70:
                colors.append('#4CAF50')
            elif acc >= 40:
                colors.append('#FF9800')
            else:
                colors.append('#F44336')

        bars = plt.bar(problem_numbers, accuracies, color=colors, edgecolor='black', linewidth=1.5)

        plt.xlabel('Номер задачи', fontsize=13, fontweight='bold')
        plt.ylabel('Точность (%)', fontsize=13, fontweight='bold')
        plt.title('Общая точность по типам задач', fontsize=16, fontweight='bold', pad=20)
        plt.xticks(problem_numbers)
        plt.ylim(0, 100)
        plt.grid(axis='y', alpha=0.3, linestyle='--')

        for bar, acc in zip(bars, accuracies):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2., height + 1,
                     f'{acc:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

        avg_global_accuracy = global_stats['overall_accuracy']
        plt.axhline(y=avg_global_accuracy, color='#2196F3', linestyle='--',
                    linewidth=2, alpha=0.7, label=f'Средняя: {avg_global_accuracy:.1f}%')

        plt.legend(loc='upper right')

        ax = plt.gca()
        ax.set_facecolor('#f8f9fa')

        plt.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()

        return base64.b64encode(image_png).decode('utf-8')

    except Exception as e:
        print(f"Ошибка при генерации глобального графика точности: {e}")
        return None


def generate_global_comparison_chart():
    try:
        global_stats = get_global_statistics()

        problem_numbers = list(range(1, 13))
        total_attempts = []
        correct_attempts = []

        for i in problem_numbers:
            stats = global_stats['problems_by_type'].get(str(i), {'total': 0, 'correct': 0})
            total_attempts.append(stats['total'])
            correct_attempts.append(stats['correct'])

        fig, ax1 = plt.subplots(figsize=(14, 7))

        bars = ax1.bar(problem_numbers, total_attempts, color='#2196F3', alpha=0.7, label='Всего попыток')

        ax2 = ax1.twinx()
        ax2.plot(problem_numbers, correct_attempts, color='#4CAF50',
                 marker='s', linewidth=3, markersize=8, label='Правильные решения')

        ax1.set_xlabel('Номер задачи', fontsize=13, fontweight='bold')
        ax1.set_ylabel('Количество попыток', fontsize=13, fontweight='bold', color='#2196F3')
        ax2.set_ylabel('Правильные решения', fontsize=13, fontweight='bold', color='#4CAF50')

        ax1.tick_params(axis='y', labelcolor='#2196F3')
        ax2.tick_params(axis='y', labelcolor='#4CAF50')

        plt.title('Сравнение: попытки vs правильные решения', fontsize=16, fontweight='bold', pad=20)
        plt.xticks(problem_numbers)

        for bar, total in zip(bars, total_attempts):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2., height + max(total_attempts) * 0.01,
                     f'{total}', ha='center', va='bottom', fontsize=9)

        for i, correct in enumerate(correct_attempts):
            ax2.text(problem_numbers[i], correct + max(correct_attempts) * 0.02,
                     f'{correct}', ha='center', va='bottom', fontsize=9, fontweight='bold', color='#2E7D32')

        lines_1, labels_1 = ax1.get_legend_handles_labels()
        lines_2, labels_2 = ax2.get_legend_handles_labels()
        ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')

        plt.grid(axis='x', alpha=0.3)
        plt.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()

        return base64.b64encode(image_png).decode('utf-8')

    except Exception as e:
        print(f"Ошибка при генерации графика сравнения: {e}")
        return None


def get_data_source_info():
    total_problems = Problem.objects.count()
    total_attempts = UserProblemAttempt.objects.count()
    updated_at = timezone.now().strftime("%d.%m.%Y %H:%M")

    return {
        'total_problems': total_problems,
        'total_attempts': total_attempts,
        'updated_at': updated_at
    }


def global_statistics(request):
    global_stats = get_global_statistics()

    graph_image = generate_global_accuracy_chart()

    comparison_image = generate_global_comparison_chart()

    user_session = request.session.session_key
    if user_session:
        user_vs_global_image = generate_user_vs_global_chart(user_session, global_stats)
    else:
        user_vs_global_image = None

    data_source = get_data_source_info()

    problem_stats = []
    problems = Problem.objects.all()
    for problem in problems:
        stats = problem.stats
        if stats['total_attempts'] >= 1:
            problem_stats.append({
                'problem': problem,
                'stats': stats,
                'accuracy': stats['accuracy']
            })

    difficult_problems = sorted(problem_stats, key=lambda x: x['accuracy'])[:10]
    easy_problems = sorted(problem_stats, key=lambda x: x['accuracy'], reverse=True)[:10]

    active_users = UserStatistics.objects.filter(
        total_attempts__gt=0
    ).order_by('-total_attempts')[:10]

    recent_successes = UserProblemAttempt.objects.filter(
        is_correct=True
    ).select_related('problem').order_by('-created_at')[:10]

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
        'graph_image': graph_image,
        'comparison_image': comparison_image,
        'user_vs_global_image': user_vs_global_image,
        'data_source': data_source,
    })


def generate_user_vs_global_chart(session_key, global_stats):
    try:
        user_stats = UserStatistics.objects.get(session_key=session_key)

        problem_numbers = list(range(1, 13))
        user_accuracies = []
        global_accuracies = []

        for i in problem_numbers:
            user_type = user_stats.get_type_statistics(i)
            global_type = global_stats['problems_by_type'].get(str(i), {'accuracy': 0})
            user_accuracies.append(user_type['accuracy'])
            global_accuracies.append(global_type['accuracy'])

        fig, ax = plt.subplots(figsize=(14, 7))

        x = np.arange(len(problem_numbers))
        width = 0.35

        bars1 = ax.bar(x - width / 2, user_accuracies, width,
                       label='Ваша точность', color='#4CAF50', edgecolor='black')
        bars2 = ax.bar(x + width / 2, global_accuracies, width,
                       label='Общая точность', color='#2196F3', edgecolor='black', alpha=0.7)

        ax.set_xlabel('Номер задачи', fontsize=13, fontweight='bold')
        ax.set_ylabel('Точность (%)', fontsize=13, fontweight='bold')
        ax.set_title('Сравнение вашей точности с общей точностью', fontsize=16, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(problem_numbers)
        ax.set_ylim(0, 100)
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        ax.legend(loc='upper right')

        def autolabel(bars):
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.annotate(f'{height:.1f}%',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom', fontsize=9,
                                fontweight='bold' if height >= 50 else 'normal')

        autolabel(bars1)
        autolabel(bars2)

        for i in range(len(problem_numbers)):
            user_acc = user_accuracies[i]
            global_acc = global_accuracies[i]
            diff = user_acc - global_acc

            if abs(diff) > 5:
                diff_color = '#2E7D32' if diff > 0 else '#C62828'
                diff_text = f"+{diff:.1f}%" if diff > 0 else f"{diff:.1f}%"

                y_pos = max(user_acc, global_acc) + 5
                ax.annotate(diff_text,
                            xy=(i, y_pos),
                            xytext=(0, 0),
                            textcoords="offset points",
                            ha='center', va='bottom',
                            fontsize=10, fontweight='bold',
                            color=diff_color)

        plt.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()

        return base64.b64encode(image_png).decode('utf-8')

    except UserStatistics.DoesNotExist:
        return None
    except Exception as e:
        print(f"Ошибка при генерации графика сравнения пользователя с общей статистикой: {e}")
        return None


def generate_user_accuracy_chart(session_key):
    try:
        user_stats = UserStatistics.objects.get(session_key=session_key)

        problem_numbers = list(range(1, 13))
        user_accuracies = []

        for i in problem_numbers:
            type_stats = user_stats.get_type_statistics(i)
            user_accuracies.append(type_stats['accuracy'])

        plt.figure(figsize=(14, 7))

        colors = []
        for acc in user_accuracies:
            if acc >= 70:
                colors.append('#4CAF50')
            elif acc >= 40:
                colors.append('#FF9800')
            else:
                colors.append('#F44336')

        bars = plt.bar(problem_numbers, user_accuracies, color=colors, edgecolor='black', linewidth=1.5)

        plt.xlabel('Номер задачи', fontsize=13, fontweight='bold')
        plt.ylabel('Точность (%)', fontsize=13, fontweight='bold')
        plt.title('Моя точность по типам задач', fontsize=16, fontweight='bold', pad=20)
        plt.xticks(problem_numbers)
        plt.ylim(0, 100)
        plt.grid(axis='y', alpha=0.3, linestyle='--')

        for bar, acc in zip(bars, user_accuracies):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2., height + 1,
                     f'{acc:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

        plt.axhline(y=user_stats.accuracy, color='#2196F3', linestyle='--',
                    linewidth=2, alpha=0.7, label=f'Средняя: {user_stats.accuracy:.1f}%')

        plt.legend(loc='upper right')

        ax = plt.gca()
        ax.set_facecolor('#f8f9fa')

        plt.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()

        return base64.b64encode(image_png).decode('utf-8')

    except Exception as e:
        print(f"Ошибка при генерации графика точности пользователя: {e}")
        return None


def generate_user_comparison_chart(session_key):
    try:
        user_stats = UserStatistics.objects.get(session_key=session_key)
        global_stats = get_global_statistics()

        problem_numbers = list(range(1, 13))
        user_accuracies = []
        global_accuracies = []

        for i in problem_numbers:
            user_type = user_stats.get_type_statistics(i)
            global_type = global_stats['problems_by_type'].get(str(i), {'accuracy': 0})
            user_accuracies.append(user_type['accuracy'])
            global_accuracies.append(global_type['accuracy'])

        x = np.arange(len(problem_numbers))
        width = 0.35

        fig, ax = plt.subplots(figsize=(14, 7))

        bars1 = ax.bar(x - width / 2, user_accuracies, width,
                       label='Моя точность', color='#4CAF50', edgecolor='black')
        bars2 = ax.bar(x + width / 2, global_accuracies, width,
                       label='Общая точность', color='#2196F3', edgecolor='black', alpha=0.7)

        ax.set_xlabel('Номер задачи', fontsize=13, fontweight='bold')
        ax.set_ylabel('Точность (%)', fontsize=13, fontweight='bold')
        ax.set_title('Сравнение: моя точность vs общая точность', fontsize=16, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(problem_numbers)
        ax.set_ylim(0, 100)
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        ax.legend()

        def autolabel(bars):
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:.1f}%',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=9)

        autolabel(bars1)
        autolabel(bars2)

        plt.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()

        return base64.b64encode(image_png).decode('utf-8')

    except Exception as e:
        print(f"Ошибка при генерации графика сравнения: {e}")
        return None


def user_statistics(request):
    user_stats = get_or_create_user_statistics(request)
    global_stats = get_global_statistics()

    progress_image = generate_progress_chart(request)
    accuracy_image = generate_user_accuracy_chart(request.session.session_key)
    comparison_image = generate_user_comparison_chart(request.session.session_key)

    data_source = get_data_source_info()

    recent_attempts = UserProblemAttempt.objects.filter(
        session_key=request.session.session_key
    ).select_related('problem').order_by('-created_at')[:20]

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

    user_attempts_by_problem = UserProblemAttempt.objects.filter(
        session_key=request.session.session_key
    ).values('problem').annotate(
        total=Count('id'),
        correct=Count('id', filter=Q(is_correct=True))
    )

    difficult_problems_data = []
    for attempt in user_attempts_by_problem:
        if attempt['total'] > 0:
            try:
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
            except Problem.DoesNotExist:
                continue

    difficult_problems = sorted(difficult_problems_data, key=lambda x: x['accuracy'])[:5]

    week_ago = timezone.now() - timedelta(days=7)
    weekly_attempts = UserProblemAttempt.objects.filter(
        session_key=request.session.session_key,
        created_at__gte=week_ago
    )

    weekly_correct = weekly_attempts.filter(is_correct=True).count()
    weekly_total = weekly_attempts.count()
    weekly_accuracy = round((weekly_correct / weekly_total * 100), 1) if weekly_total > 0 else 0

    two_weeks_ago = timezone.now() - timedelta(days=14)
    prev_weekly_attempts = UserProblemAttempt.objects.filter(
        session_key=request.session.session_key,
        created_at__range=[two_weeks_ago, week_ago]
    )

    prev_weekly_correct = prev_weekly_attempts.filter(is_correct=True).count()
    prev_weekly_total = prev_weekly_attempts.count()
    prev_weekly_accuracy = round((prev_weekly_correct / prev_weekly_total * 100), 1) if prev_weekly_total > 0 else 0

    change = 0
    if prev_weekly_accuracy > 0:
        change = round(weekly_accuracy - prev_weekly_accuracy, 1)

    return render(request, 'home/user_statistics.html', {
        'user_stats': user_stats,
        'global_stats': global_stats,
        'recent_attempts': recent_attempts,
        'type_stats': type_stats,
        'difficult_problems': difficult_problems,
        'progress_image': progress_image,
        'accuracy_image': accuracy_image,
        'comparison_image': comparison_image,
        'data_source': data_source,
        'weekly_stats': {
            'total': weekly_total,
            'correct': weekly_correct,
            'accuracy': weekly_accuracy,
            'change': change
        }
    })


def check_problem(request):
    if request.method == 'POST':
        problem_id = request.POST.get('problem_id')
        ege_number = request.POST.get('ege_number')
        user_answer = request.POST.get('user_answer')

        problem = Problem.objects.get(id=problem_id)

        try:
            user_answer_float = float(user_answer)
            correct_answer_float = float(problem.answer)
            is_correct = abs(user_answer_float - correct_answer_float) < 0.01
        except (ValueError, TypeError):
            is_correct = False

        result = {
            'problem_id': int(problem_id),
            'user_answer': user_answer,
            'correct_answer': problem.answer,
            'is_correct': is_correct
        }

        return problems_by_number(request, ege_number, result)

    return redirect('all_numbers')


def problems_by_number(request, ege_number, result=None):
    problems = Problem.objects.filter(ege_number=ege_number)

    context = {
        'problems': problems,
        'ege_number': ege_number,
        'total': problems.count(),
        'result': result
    }

    return render(request, 'home/problems_by_number.html', context)
