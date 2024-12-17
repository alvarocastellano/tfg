from django.urls import path
from . import views

app_name = 'community'


urlpatterns = [
    path('all_chats/', views.all_chats, name='all_chats'),
    path('create_private_chat/', views.create_private_chat, name='create_private_chat'),
]