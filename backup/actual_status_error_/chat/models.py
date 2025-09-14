# chat/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q

class Room(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages',
        null=True,  # Allow direct messages to have no recipient
        blank=True,
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='messages',
        null=True,  # Allow room messages to have no room
        blank=True,
    )
    content = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        constraints = [
            models.CheckConstraint(
                check=Q(recipient__isnull=True, room__isnull=False) | Q(recipient__isnull=False, room__isnull=True),
                name='either_recipient_or_room_is_set',
            )
        ]



User.add_to_class('last_seen', models.DateTimeField(null=True, blank=True))