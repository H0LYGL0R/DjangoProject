from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('choose/', views.choose_mode, name='choose_mode'),
    path('variant/', views.full_variant, name='full_variant'),
    path('check_variant/', views.check_variant, name='check_variant'),
    path('numbers/', views.all_numbers, name='all_numbers'),
    path('result/', views.show_result, name='show_result'),
    path('number/<int:ege_number>/', views.problems_by_number, name='problems_by_number'),
]