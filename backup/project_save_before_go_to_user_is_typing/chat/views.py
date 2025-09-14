# chat/views.py
from django.http import StreamingHttpResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.db import models
from asgiref.sync import sync_to_async
from .models import Message, Room
import asyncio

# ... async_login_required decorator ...

def async_login_required(view_func):
    async def wrapper(request, *args, **kwargs):
        user = await request.auser()
        if not user.is_authenticated:
            return redirect(f"/accounts/login/?next={request.path}")
        return await view_func(request, *args, **kwargs)
    return wrapper

@async_login_required
async def chat_home(request):
    """Renders the chat home page with a list of all users and rooms."""
    user = await request.auser()
    all_users = await sync_to_async(list)(User.objects.all().exclude(username=user.username))
    all_rooms = await sync_to_async(list)(Room.objects.all())
    context = {
        'user': user,
        'all_users': all_users,
        'all_rooms': all_rooms,
    }
    return render(request, 'chat/home.html', context)

@async_login_required
async def room_chat_page(request, room_name):
    """Renders the room chat interface."""
    room = await sync_to_async(get_object_or_404)(Room, slug=room_name)
    user = await request.auser()
    
    messages = await sync_to_async(list)(
        Message.objects.filter(room=room).select_related('user')
    )
    last_message_id = messages[-1].id if messages else 0

    context = {
        'messages': messages,
        'user': user,
        'room': room,
        'last_message_id': last_message_id,  # Pass this value to the template
    }
    return render(request, 'chat/room.html', context)

@async_login_required
async def room_chat_sse(request, room_name):
    """Streams new messages for a specific room."""
    room = await sync_to_async(get_object_or_404)(Room, slug=room_name)
    
    last_message_id = 0
    if 'HTTP_LAST_EVENT_ID' in request.META:
        last_message_id = int(request.META['HTTP_LAST_EVENT_ID'])
    
    async def event_stream(room, last_message_id):
        while True:
            new_messages = await sync_to_async(list)(
                Message.objects.filter(room=room, id__gt=last_message_id).select_related('user')
            )
            
            if new_messages:
                last_message_id = new_messages[-1].id
                for message in new_messages:
                    event_data = f"<p><strong>{message.user.username}:</strong> {message.content}</p>"
                    yield f"id: {message.id}\n"
                    yield f"event: new-message\n"
                    yield f"data: {event_data}\n\n".encode('utf-8')
            
            await asyncio.sleep(1)
            
    response = StreamingHttpResponse(event_stream(room, last_message_id), content_type="text/event-stream")
    response['Cache-Control'] = 'no-cache'
    return response

@csrf_exempt
@async_login_required
@sync_to_async
def room_post_message(request, room_name):
    """Receives and saves a new chat message to a specific room."""
    if request.method == "POST":
        message_content = request.POST.get("message")
        if message_content:
            user = request.user
            room = get_object_or_404(Room, slug=room_name)
            Message.objects.create(user=user, room=room, content=message_content)
    return HttpResponse("")


# ---- Direct messaging views (modified) ----

@async_login_required
async def chat_page(request, recipient_username):
    """Renders the direct messaging interface for a specific recipient."""
    recipient = await sync_to_async(get_object_or_404)(User, username=recipient_username)
    user = await request.auser()
    
    messages = await sync_to_async(list)(
        Message.objects.filter(
            (models.Q(user=user, recipient=recipient) | models.Q(user=recipient, recipient=user))
        ).select_related('user', 'recipient')
    )
    last_message_id = messages[-1].id if messages else 0
    
    context = {
        'messages': messages,
        'user': user,
        'recipient': recipient,
        'last_message_id': last_message_id,
    }
    return render(request, "chat/index.html", context)

# ... chat_sse and post_message for direct messaging can remain mostly the same ...

@async_login_required
async def chat_sse(request, recipient_username):
    """Streams new messages for a specific conversation by long-polling the database."""
    user = await request.auser()
    recipient = await sync_to_async(get_object_or_404)(User, username=recipient_username)
    
    last_message_id = 0
    if 'HTTP_LAST_EVENT_ID' in request.META:
        last_message_id = int(request.META['HTTP_LAST_EVENT_ID'])
    
    async def event_stream(user, recipient, last_message_id):
        while True:
            new_messages = await sync_to_async(list)(
                Message.objects.filter(
                    (
                        (models.Q(user=user, recipient=recipient) | models.Q(user=recipient, recipient=user))
                    ) & models.Q(id__gt=last_message_id)
                ).select_related('user', 'recipient')
            )
            
            if new_messages:
                last_message_id = new_messages[-1].id
                
                for message in new_messages:
                    event_data = f"<p><strong>{message.user.username}:</strong> {message.content}</p>"
                    yield f"id: {message.id}\n"
                    yield f"event: new-message\n"
                    yield f"data: {event_data}\n\n".encode('utf-8')
            
            await asyncio.sleep(1)

    response = StreamingHttpResponse(event_stream(user, recipient, last_message_id), content_type="text/event-stream")
    response['Cache-Control'] = 'no-cache'
    return response

@csrf_exempt
@async_login_required
@sync_to_async
def post_message(request, recipient_username):
    """Receives and saves a new chat message to the database."""
    if request.method == "POST":
        message_content = request.POST.get("message")
        if message_content:
            user = request.user
            recipient = get_object_or_404(User, username=recipient_username)
            Message.objects.create(user=user, recipient=recipient, content=message_content)
    return HttpResponse("")
