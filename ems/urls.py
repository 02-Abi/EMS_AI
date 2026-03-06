from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('employees/', include('employees.urls')),
    path('performance/', include('performance.urls')),
    path('audit/', include('audit.urls')),
    path('', views.dashboard, name='dashboard'),
     path('ml/', include('ml_engine.urls')), 
]