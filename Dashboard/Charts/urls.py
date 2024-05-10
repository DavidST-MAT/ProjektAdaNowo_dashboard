from django.urls import path
from . import views
from .views import handle_time_range



urlpatterns = [
    path('', views.index, name="index"),
    path('Charts/updateChartOneMinute/', views.updateChartOneMinute, name='updateChartOneMinute'),
    path('Charts/update_ambient_temperature_chart/', views.update_ambient_temperature_chart, name='update_ambient_temperature_chart'),
    path('Adanowo/update/', handle_time_range, name='handle_time_range')
]