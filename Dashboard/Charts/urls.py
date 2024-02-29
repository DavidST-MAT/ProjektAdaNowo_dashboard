from django.urls import path
from . import views



urlpatterns = [
    path('', views.index, name="index"),

    path('Charts/updateChartOneMinute/', views.updateChartOneMinute, name='updateChartOneMinute'),

    path('time/', views.time, name='time'),
    path('dashboard/', views.dashboard, name='dashboard'),
]