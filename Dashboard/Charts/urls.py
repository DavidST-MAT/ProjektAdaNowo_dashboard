from django.urls import path
from . import views
from .views import handle_time_range



urlpatterns = [
    path('', views.index, name="index"),
    path('Charts/update_nonwoven_unevenness_chart/', views.update_nonwoven_unevenness_chart, name='update_nonwoven_unevenness_chart'),
    path('Charts/update_card_floor_evenness_chart/', views.update_card_floor_evenness_chart, name='update_card_floor_evenness_chart'),
    path('Charts/update_ambient_temperature_chart/', views.update_ambient_temperature_chart, name='update_ambient_temperature_chart'),
    path('Charts/update_humidity_environment_chart/', views.update_humidity_environment_chart, name='update_humidity_environment_chart'),
    path('Adanowo/update/', handle_time_range, name='handle_time_range')
]