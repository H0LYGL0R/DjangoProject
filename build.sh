#!/usr/bin/env bash
# build.sh
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

python -c "
from home.models import Problem
if Problem.objects.count() == 0:
    problems = [
        {'text': 'Найдите 15% от 80', 'answer': 12},
        {'text': 'Решите: 2x² - 5x + 3 = 0', 'answer': 1.5},
        {'text': '√144', 'answer': 12},
        {'text': '2 + 2 × 2', 'answer': 6},
        {'text': 'Площадь круга с радиусом 3', 'answer': 28.27},
        {'text': 'sin(30°)', 'answer': 0.5},
        {'text': 'log₂(8)', 'answer': 3},
    ]
    for p in problems:
        Problem.objects.create(**p)
"