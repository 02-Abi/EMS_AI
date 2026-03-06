from django.urls import path
from . import views

app_name = 'performance'

urlpatterns = [
    path('', views.performance_list, name='list'),
    path('create/', views.performance_create, name='create'),
    path('<int:pk>/', views.performance_detail, name='detail'),
    path('<int:pk>/update/', views.performance_update, name='update'),
    path('<int:pk>/delete/', views.performance_delete, name='delete'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('department-average/', views.department_average, name='department_avg'),
]