from django.contrib import admin
from .models import User, Post, Comment
from .models import Notification, Message


admin.site.register([
    User, Post, Comment,
    Notification, Message
])