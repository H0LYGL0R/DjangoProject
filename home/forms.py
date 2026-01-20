from django import forms
from .models import Problem, UserProblemAttempt


class OptionalFloatField(forms.FloatField):
    def clean(self, value):
        try:
            return super().clean(value)
        except forms.ValidationError:
            if not self.required:
                return None
            raise


class SingleProblemForm(forms.Form):
    problem_id = forms.IntegerField(widget=forms.HiddenInput())
    ege_number = forms.IntegerField(widget=forms.HiddenInput())
    user_answer = OptionalFloatField(
        label='Ваш ответ',
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ответ',
            'step': '0.01'
        })
    )


class VariantForm(forms.Form):

    def __init__(self, *args, **kwargs):
        problems = kwargs.pop('problems', [])
        super().__init__(*args, **kwargs)

        for problem in problems:
            field_name = f'answer_{problem.id}'
            self.fields[field_name] = OptionalFloatField(
                label=f'Задача {problem.ege_number}',
                required=False,
                widget=forms.NumberInput(attrs={
                    'class': 'form-control variant-answer',
                    'placeholder': 'Ответ',
                    'step': '0.01'
                })
            )
            self.fields[field_name].problem = problem


class ProblemFilterForm(forms.Form):
    TYPE_CHOICES = [
        ('', 'Все типы'),
        ('1', 'Задача 1'),
        ('2', 'Задача 2'),
        ('3', 'Задача 3'),
        ('4', 'Задача 4'),
        ('5', 'Задача 5'),
        ('6', 'Задача 6'),
        ('7', 'Задача 7'),
        ('8', 'Задача 8'),
        ('9', 'Задача 9'),
        ('10', 'Задача 10'),
        ('11', 'Задача 11'),
        ('12', 'Задача 12'),
    ]

    problem_type = forms.ChoiceField(
        choices=TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'onchange': 'this.form.submit()'
        })
    )

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по условию...'
        })
    )


class StatisticsFilterForm(forms.Form):
    PERIOD_CHOICES = [
        ('all', 'За все время'),
        ('week', 'За неделю'),
        ('month', 'За месяц'),
        ('year', 'За год'),
    ]

    period = forms.ChoiceField(
        choices=PERIOD_CHOICES,
        initial='all',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'onchange': 'this.form.submit()'
        })
    )

    problem_type = forms.ChoiceField(
        choices=[('', 'Все задачи')] + ProblemFilterForm.TYPE_CHOICES[1:],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'onchange': 'this.form.submit()'
        })
    )


class UserSettingsForm(forms.Form):
    show_hints = forms.BooleanField(
        label='Показывать подсказки',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    auto_check = forms.BooleanField(
        label='Автопроверка ответов',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    difficulty_level = forms.ChoiceField(
        label='Уровень сложности',
        choices=[
            ('beginner', 'Начинающий'),
            ('intermediate', 'Средний'),
            ('advanced', 'Продвинутый'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )


class ContactForm(forms.Form):
    name = forms.CharField(
        label='Имя',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ваше имя'
        })
    )

    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ваш email'
        })
    )

    message = forms.CharField(
        label='Сообщение',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Ваше сообщение или предложение'
        })
    )

    problem_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput()
    )


class ReportProblemForm(forms.Form):
    ERROR_TYPE_CHOICES = [
        ('wrong_answer', 'Неверный ответ'),
        ('wrong_condition', 'Ошибка в условии'),
        ('typo', 'Опечатка'),
        ('other', 'Другое'),
    ]

    error_type = forms.ChoiceField(
        label='Тип ошибки',
        choices=ERROR_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    description = forms.CharField(
        label='Описание',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Подробно опишите ошибку...'
        })
    )

    correct_answer = forms.CharField(
        label='Правильный ответ (если знаете)',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Правильный ответ'
        })
    )

    problem_id = forms.IntegerField(
        widget=forms.HiddenInput()
    )
