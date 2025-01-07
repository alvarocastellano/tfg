from django.urls import path
from . import views

app_name = 'community'


urlpatterns = [
    path('all_chats/', views.all_chats, name='all_chats'),
    path('create_private_chat/', views.create_private_chat, name='create_private_chat'),
    path('chat_requests/', views.chat_requests, name='chat_requests'),
    path('accept_chat_request/<int:request_id>/', views.accept_chat_request, name='accept_chat_request'),
    path('reject_chat_request/<int:request_id>/', views.reject_chat_request, name='reject_chat_request'),
    path('chat_detail/<str:username>/', views.chat_detail, name='chat_detail'),
    path('chat/<str:city>/', views.city_group_chat, name='city_group_chat'),
    path('create_group_chat/', views.create_group_chat, name='create_group_chat'),
    path('chat/<str:name>/', views.group_chat_details, name='group_chat_details'),
    path('delete_group/<str:name>/', views.delete_group, name='delete_group'),
    path('chat/<str:username>/request_deletion/', views.request_chat_deletion, name='request_chat_deletion'),
    path('leave_group/<str:name>/', views.leave_group, name='leave_group'),

]