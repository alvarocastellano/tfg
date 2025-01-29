from django.urls import path
from . import views

app_name = 'turism'

urlpatterns = [
    path('city_map/<str:city_name>/', views.city_map, name='city_map'),
]