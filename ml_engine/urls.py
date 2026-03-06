from django.urls import path
from . import views

app_name = 'ml_engine'

urlpatterns = [
    path('', views.ml_dashboard, name='dashboard'),
    path('train/', views.train_models, name='train'),
    # Remove the predict line – it's not needed for basic functionality
]