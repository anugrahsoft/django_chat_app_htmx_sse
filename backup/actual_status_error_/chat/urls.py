# chat/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_home, name='chat_home'),
    path('dm/<str:recipient_username>/', views.chat_page, name='dm_chat_page'),
    path('dm/<str:recipient_username>/sse/', views.chat_sse, name='dm_chat_sse'),
    path('dm/<str:recipient_username>/post/', views.post_message, name='dm_post_message'),
    path('room/<str:room_name>/', views.room_chat_page, name='room_chat_page'),
    path('room/<str:room_name>/sse/', views.room_chat_sse, name='room_chat_sse'),
    path('room/<str:room_name>/post/', views.room_post_message, name='room_post_message'),

    path('update-last-seen/', views.update_last_seen, name='update_last_seen'),
    
]
