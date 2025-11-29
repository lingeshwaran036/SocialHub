from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class User(models.Model):
    username = models.CharField(max_length=150, unique=True)
    name = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to='profile/', blank=True, null=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    friends = models.ManyToManyField("self", symmetrical=True, blank=True)
    saved_posts = models.ManyToManyField('Post', related_name='saved_by', blank=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def add_friend(self, user):
        if user != self:
            self.friends.add(user)

    def remove_friend(self, user):
        self.friends.remove(user)

    def is_friend(self, user):
        return self.friends.filter(id=user.id).exists()

    def __str__(self):
        return self.username


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    image = models.ImageField(upload_to='posts/')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)

    def add_like(self, user):
        self.likes.add(user)

    def remove_like(self, user):
        self.likes.remove(user)

    def is_liked(self, user):
        return self.likes.filter(id=user.id).exists()

    def add_comment(self, user, text):
        return Comment.objects.create(post=self, user=user, text=text)

    def remove_comment(self, comment_id):
        Comment.objects.filter(id=comment_id, post=self).delete()

    def comment_count(self):
        return self.comments.count()

    def get_comments(self):
        return self.comments.all()

    def __str__(self):
        return f"{self.user.username}'s Post"


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.text[:30]}"


class Notification(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_notifications")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_notifications")
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username}: {self.message}"


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")

    text = models.TextField(blank=True, null=True)  # ← FIXED
    attachment = models.FileField(upload_to='messages/', blank=True, null=True)

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username}"