# chat/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_home, name='chat_home'), # Use the new view here
    path('<str:recipient_username>/', views.chat_page, name='chat_page'),
    path('<str:recipient_username>/sse/', views.chat_sse, name='chat_sse'),
    path('<str:recipient_username>/post/', views.post_message, name='post_message'),
]
