from .models import Notification, User
from django.http import HttpRequest

def create_notification(sender: User, receiver: User, message: str, link: str = None):
    if not isinstance(sender, User) or not isinstance(receiver, User):
        raise ValueError("sender and receiver must be User instances")
    Notification.objects.create(
        sender=sender,
        receiver=receiver,
        message=message,
        link=link
    )


def notification_count(request: HttpRequest):
    user_id = request.session.get("user_id")
    if not user_id:
        return {'notification_count': 0}

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {'notification_count': 0}

    unread = Notification.objects.filter(receiver=user, is_read=False).count()
    return {'notification_count': unread}