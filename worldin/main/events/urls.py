from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('calendar/city=<str:selected_city>/', views.event_calendar, name='event_calendar'),
    path('create/city=<str:selected_city>/', views.create_event, name='create_event'),
    path('edit/<int:pk>/', views.edit_event, name='edit_event'),
]
