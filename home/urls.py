from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('choose/', views.choose_mode, name='choose_mode'),
    path('variant/', views.full_variant, name='full_variant'),
    path('check-variant/', views.check_variant, name='check_variant'),
    path('result/', views.show_result, name='show_result'),
    path('numbers/', views.all_numbers, name='all_numbers'),
    path('number/<int:ege_number>/', views.problems_by_number, name='problems_by_number'),
    path('user-statistics/', views.user_statistics, name='user_statistics'),
    path('global-statistics/', views.global_statistics, name='global_statistics'),
    path('check-problem/', views.check_problem, name='check_problem'),
    path('number/<int:ege_number>/', views.problems_by_number, name='problems_by_number')
]