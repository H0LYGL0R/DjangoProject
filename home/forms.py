# ege/forms.py

from django import forms
from .models import Problem, UserAttempt


class ProblemSolveForm(forms.ModelForm):
    """Форма для решения задачи"""

    user_answer = forms.DecimalField(
        label="Ваш ответ",
        max_digits=10,
        decimal_places=2,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите число',
            'step': '0.01'
        })
    )

    class Meta:
        model = UserAttempt
        fields = ['user_answer']

    def clean_user_answer(self):
        """Валидация ответа"""
        user_answer = self.cleaned_data.get('user_answer')
        if user_answer is None:
            raise forms.ValidationError("Пожалуйста, введите ответ")
        return user_answer