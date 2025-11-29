from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages as django_messages
from .models import User, Post, Comment, Notification, Message
from django.core.paginator import Paginator
from .utils import create_notification
from django.contrib import messages

def get_current_user(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return get_object_or_404(User, id=user_id)


def home(request):
    user = get_current_user(request)
    if not user:
        return redirect("login")
    posts = Post.objects.all().order_by("-created_at")
    return render(request, "Home/index.html", {"user": user, "posts": posts})


def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = User.objects.filter(username=username, password=password).first()
        if user:
            request.session["user_id"] = user.id
            django_messages.success(request, "Logged in successfully.")
            return redirect("home")
        else:
            django_messages.error(request, "Invalid credentials.")
            return redirect("login")
    return render(request, "Home/login.html")


def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        name = request.POST.get("name")
        photo = request.FILES.get("photo")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(email=email).exists():
            django_messages.error(request, "Email already exists.")
            return redirect("register")
        if User.objects.filter(username=username).exists():
            django_messages.error(request, "Username already taken.")
            return redirect("register")

        user = User.objects.create(username=username, name=name, photo=photo, email=email, password=password)
        django_messages.success(request, "Account created successfully.")
        return redirect("login")
    return render(request, "Home/register.html")


def logout(request):
    request.session.flush()
    django_messages.success(request, "Logged out successfully.")
    return redirect("login")


def search_user(request):
    query = request.GET.get('q', '')
    user_list = User.objects.filter(username__icontains=query).order_by('username') if query else User.objects.none()
    paginator = Paginator(user_list, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'Profile/search_user.html', {'query': query, 'page_obj': page_obj})
        

def create_post(request):
    user = get_current_user(request)
    if not user:
        return redirect("login")

    if request.method == "POST":
        image = request.FILES.get("image")
        description = request.POST.get("description")
        Post.objects.create(user=user, image=image, description=description)
        django_messages.success(request, "Post created successfully.")
        return redirect("home")
    return render(request, "Post/create_post.html")


def save_post(request, post_id):
    user = get_current_user(request)
    if not user:
        return redirect("login")
    post = get_object_or_404(Post, id=post_id)
    if post in user.saved_posts.all():
        user.saved_posts.remove(post)
        django_messages.info(request, "Post removed from saved.")
    else:
        user.saved_posts.add(post)
        django_messages.success(request, "Post saved.")
    return redirect("home")


def saved_posts(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    user = get_object_or_404(User, id=user_id)
    posts = user.saved_posts.all().order_by("-created_at")  # latest first

    return render(request, "Post/saved_posts.html", {
        "user": user,
        "posts": posts,
    })
    

def view_post(request, post_id):
    user = get_current_user(request)
    if not user:
        return redirect("login")
    post = get_object_or_404(Post, id=post_id)
    comments = post.get_comments().order_by("created_at")

    if request.method == "POST":
        text = request.POST.get("comment")
        if text:
            post.add_comment(user, text)
            if post.user != user:
                create_notification(sender=user, receiver=post.user, message=f"{user.username} commented on your post", link=f"/post/{post.id}/")
            return redirect("view_post", post_id=post_id)

    return render(request, "Post/view_post.html", {"user": user, "post": post, "comments": comments})


def edit_post(request, post_id):
    user = get_current_user(request)
    if not user:
        return redirect("login")
    post = get_object_or_404(Post, id=post_id)
    if post.user != user:
        django_messages.error(request, "You cannot edit this post.")
        return redirect("home")

    if request.method == "POST":
        description = request.POST.get("description")
        if "image" in request.FILES:
            post.image = request.FILES["image"]
        post.description = description
        post.save()
        django_messages.success(request, "Post updated successfully.")
        return redirect("home")
    return render(request, "Post/edit_post.html", {"post": post, "user": user})


def delete_post(request, post_id):
    user = get_current_user(request)
    if not user:
        return redirect("login")
    post = get_object_or_404(Post, id=post_id)
    if post.user != user:
        django_messages.error(request, "You cannot delete this post.")
        return redirect("home")
    post.delete()
    django_messages.success(request, "Post deleted successfully.")
    return redirect("home")


def like_post(request, post_id):
    user = get_current_user(request)
    if not user:
        return redirect("login")
        
    post = get_object_or_404(Post, id=post_id)
    if post.is_liked(user):
        post.remove_like(user)
    else:
        post.add_like(user)
        
        if post.user != user:
            create_notification(sender=user, receiver=post.user, message=f"{user.username} liked your post", link=f"/post/{post.id}/")
    return redirect("home")


def add_comment(request, post_id):
    user = get_current_user(request)
    if not user:
        return redirect("login")
    post = get_object_or_404(Post, id=post_id)
    text = request.POST.get("text")
    if text:
        post.add_comment(user, text)
        if post.user != user:
            create_notification(sender=user, receiver=post.user, message=f"{user.username} commented on your post", link=f"/post/{post.id}/")
    return redirect("view_post", post_id=post_id)


def delete_comment(request, comment_id):
    user = get_current_user(request)
    if not user:
        return redirect("login")
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.user == user:
        comment.post.remove_comment(comment.id)
    return redirect("home")


def profile(request):
    user = get_current_user(request)
    if not user:
        return redirect("login")
    posts = Post.objects.filter(user=user).order_by("-created_at")
    saved_posts = user.saved_posts.all()
    return render(request, "Profile/profile.html", {"user": user, "posts": posts, "saved_posts": saved_posts})


def edit_profile(request):
    user = get_current_user(request)
    if not user:
        return redirect('login')

    if request.method == 'POST':
        username = request.POST.get('username')
        name = request.POST.get('name')
        email = request.POST.get('email')
        bio = request.POST.get('bio')
        photo = request.FILES.get('photo')
        
        if User.objects.exclude(id=user.id).filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return redirect('edit_profile')
        if User.objects.exclude(id=user.id).filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return redirect('edit_profile')
            
        user.username = username
        user.name = name
        user.email = email
        user.bio = bio
        if photo:
            user.photo = photo
        user.save()

        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')

    return render(request, 'Profile/edit_profile.html', {'user': user})
        
        
def view_profile(request, user_id):
    current_user = get_current_user(request)
    profile_user = get_object_or_404(User, id=user_id)
    posts = Post.objects.filter(user=profile_user).order_by("-created_at")
    is_friend = current_user.is_friend(profile_user) if current_user else False
    return render(request, "Profile/view_profile.html", {"user": current_user, "profile_user": profile_user, "posts": posts, "is_friend": is_friend})


def friend(request, user_id):
    user = get_current_user(request)
    if not user:
        return redirect("login")
        
    profile_user = get_object_or_404(User, id=user_id)
    user.friends.add(profile_user)
    create_notification(sender=user, receiver=profile_user, message=f"{user.username} added you as a friend", link=f"/profile/{user.id}/friends/")
    return redirect("view_profile", user_id=profile_user.id)


def unfriend(request, user_id):
    user = get_current_user(request)
    if not user:
        return redirect("login")
        
    other_user = get_object_or_404(User, id=user_id)
    user.remove_friend(other_user)
    return redirect("view_profile", user_id=user_id)


def view_friends(request, user_id):
    profile_user = get_object_or_404(User, id=user_id)
    friends = profile_user.friends.all()
    current_user = None
    friend_ids = []

    if 'user_id' in request.session:
        current_user = get_object_or_404(User, id=request.session['user_id'])
        friend_ids = [f.id for f in current_user.friends.all()]

    context = {
        "profile_user": profile_user,
        "friends": friends,
        "current_user": current_user,
        "friends_statuses": {"friend_ids": friend_ids},
    }
    return render(request, "Profile/friends_list.html", context)
    

def notifications(request):
    user = get_current_user(request)
    notes = Notification.objects.filter(receiver=user).order_by("-created_at") if user else []
    return render(request, "Profile/notifications.html", {"notifications": notes})


def messages_page(request):
    user = get_current_user(request)
    if not user:
        return redirect("login")

    # FRIEND LIST
    friends = user.friends.all()

    # SEARCH FRIENDS
    query = request.GET.get("q", "")
    if query:
        friends = friends.filter(username__icontains=query)

    # CURRENT CHAT USER
    chat_with_id = request.GET.get("chat")
    chat_with = None
    messages_list = []

    if chat_with_id:
        chat_with = get_object_or_404(User, id=chat_with_id)

        # Make sure chat target is actually a friend
        if chat_with not in friends:
            chat_with = None  
        else:
            # Load chat messages
            messages_list = Message.objects.filter(
                sender__in=[user, chat_with],
                receiver__in=[user, chat_with]
            ).order_by("created_at")

            # Mark messages as read
            Message.objects.filter(
                sender=chat_with,
                receiver=user,
                is_read=False
            ).update(is_read=True)

    # UNREAD COUNTS
    friends_unread = []
    for friend in friends:
        unread = Message.objects.filter(
            sender=friend,
            receiver=user,
            is_read=False
        ).count()
        friends_unread.append((friend, unread))

    return render(request, "Profile/messages.html", {
        "user": user,
        "friends_unread": friends_unread,
        "chat_with": chat_with,
        "messages_list": messages_list,
        "query": query,
    })


def send_message(request, receiver_id):
    user = get_current_user(request)
    if not user:
        return redirect("login")

    receiver = get_object_or_404(User, id=receiver_id)

    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        attachment = request.FILES.get("attachment")

        # Prevent empty messages (both fields empty)
        if not text and not attachment:
            return redirect(f"/messages/?chat={receiver.id}")

        # Create the message
        msg = Message.objects.create(
            sender=user,
            receiver=receiver,
            text=text,
            attachment=attachment
        )

        # Create notification safely
        try:
            create_notification(
                sender=user,
                receiver=receiver,
                message=f"{user.username} sent you a message",
                link=f"/messages/?chat={receiver.id}"
            )
        except Exception as e:
            print("Notification Error:", e)

        return redirect(f"/messages/?chat={receiver.id}")

    return redirect(f"/messages/?chat={receiver.id}")