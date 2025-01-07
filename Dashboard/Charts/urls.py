from django.urls import path
from . import views
from .views import handle_time_range

urlpatterns = [
    path('', views.index, name="index"),
    path('Charts/update_nonwoven_unevenness_chart/', views.update_nonwoven_unevenness_chart, name='update_nonwoven_unevenness_chart'),
    path('Charts/update_card_floor_evenness_chart/', views.update_card_floor_evenness_chart, name='update_card_floor_evenness_chart'),
    path('Charts/update_environmental_values_chart/', views.update_environmental_values_chart, name='update_environmental_values_chart'),
    path('Charts/update_laboratory_values_chart/', views.update_laboratory_values_chart, name='update_laboratory_values_chart'),
    path('Charts/update_tear_length_chart/', views.update_tear_length_chart, name='update_tear_length_chart'),
    path('Charts/update_economics_chart/', views.update_economics_chart, name='update_economics_chart'),
    path('Charts/update_line_power_consumption_chart/', views.update_line_power_consumption_chart, name='update_line_power_consumption_chart'),
    path('Adanowo/update/', handle_time_range, name='handle_time_range')
]

