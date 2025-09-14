from django.utils import timezone
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User

class LastSeenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    async def __call__(self, request):
        response = await self.get_response(request)
        if request.user.is_authenticated:
            # Update the last_seen timestamp directly on the database
            # This is more efficient than fetching the user object first
            await sync_to_async(User.objects.filter(pk=request.user.pk).update)(last_seen=timezone.now())
        return response
