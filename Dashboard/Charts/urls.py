from django.urls import path
from . import views
from .views import getPerformanceMeasureOneHour


urlpatterns = [
    path('', views.index, name="index"),

    path('Charts/getPerformanceMeasureOneHour/', views.getPerformanceMeasureOneHour, name='getPerformanceMeasureOneHour'),
    path('Charts/getPerformanceMeasureFourHour/', views.getPerformanceMeasureFourHour, name='getPerformanceMeasureFourHour'),

    path('energiewerte/', views.energiewerte, name='energiewerte'),
    path('energiewerte/get_energy_consumption_one_hour', views.get_energy_consumption_one_hour, name='get_energy_consumption_one_hour'),

    path('umweltwerte/', views.umweltwerte, name='umweltwerte'),
    path('umweltwerte/get_temperatur_one_hour', views.get_temperatur_one_hour, name='get_temperatur_one_hour'),
    
]