#!/usr/bin/env python3
"""
Fake data generator for SocialHub.

Creates:
- Users (writes credentials to generated_users.txt)
- Posts (images from picsum.photos)
- Friend links (mutual)
- Optional followers (if User has a field named 'followers' or 'followings')
- Random likes, saved posts, comments
- Random chat messages (Message model)
- Notifications via Notification model

Run:
    python dummy_data.py
"""

import os
import django
import random
import time
from faker import Faker
import urllib.request
from io import BytesIO
from django.core.files import File
from django.contrib.auth.hashers import make_password

# --- CONFIGURATION ---
NUM_USERS = 25                 # number of users to create
POSTS_PER_USER = 5             # posts per user
MAX_FRIENDS_PER_USER = 8      # max friends to create per user
MAX_LIKES_PER_POST = 10       # up to this many likes per post
MAX_SAVED_PER_USER = 8        # how many posts a user may save
MAX_COMMENTS_PER_POST = 6     # comments per post
MAX_MESSAGES_PER_PAIR = 10    # messages exchanged between a friend pair
OUTPUT_FILE = "generated_users.txt"
IMAGE_TIMEOUT = 10            # seconds for image downloads
# -------------------------

# point to your settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SocialHub.settings")
django.setup()

from Profile.models import User, Post, Comment, Message, Notification  # import your models

fake = Faker()


def fetch_image_bytes(url):
    """Return BytesIO or raise."""
    try:
        with urllib.request.urlopen(url, timeout=IMAGE_TIMEOUT) as resp:
            data = resp.read()
        return BytesIO(data)
    except Exception as e:
        print(f"⚠️  Image download failed ({url}): {e}")
        raise


def safe_save_image(model_field, filename, bytes_io):
    """Save a BytesIO to a model's ImageField/FileField safely."""
    bytes_io.seek(0)
    django_file = File(bytes_io)
    model_field.save(filename, django_file, save=True)


def create_notification_safe(sender, receiver, message, link=None):
    """Create Notification object if model exists and args valid."""
    try:
        # ensure sender/receiver are model instances
        if not (hasattr(sender, "id") and hasattr(receiver, "id")):
            return
        Notification.objects.create(sender=sender, receiver=receiver, message=message, link=link)
    except Exception as e:
        print(f"⚠️  Failed to create notification: {e}")


def main():
    print("🔁 Starting fake data generator...")

    # wipe or create output file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("=== Generated User Accounts ===\n\n")

    created_users = []

    # Create users
    print(f"👥 Creating {NUM_USERS} users...")
    for i in range(NUM_USERS):
        # ensure unique-ish usernames
        base = fake.user_name()
        username = f"{base}{random.randint(100,999)}"
        name = fake.name()
        email = fake.unique.email()
        raw_password = "password123"  # default password for generated users
        hashed_password = make_password(raw_password)
        bio = fake.sentence(nb_words=12)

        # Download profile image
        image_url = f"https://picsum.photos/seed/user{random.randint(1,10000)}/300"
        try:
            img_bytes = fetch_image_bytes(image_url)
        except Exception:
            img_bytes = None

        # create user instance
        user = User(username=username, name=name, bio=bio, email=email, password=hashed_password)
        user.save()  # must save before saving image to field

        if img_bytes:
            try:
                safe_save_image(user.photo, f"{username}.jpg", img_bytes)
            except Exception as e:
                print(f"⚠️ Could not save photo for {username}: {e}")

        created_users.append((user, raw_password))

        # write credentials to file
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(f"Username: {username} | Password: {raw_password}\n")

    print(f"✅ Created {len(created_users)} users. Credentials saved to {OUTPUT_FILE}")

    # Create posts
    print("🖼️ Creating posts for each user...")
    created_posts = []
    for user, _ in created_users:
        for _ in range(POSTS_PER_USER):
            description = fake.sentence(nb_words=15)
            post = Post(user=user, description=description)
            post.save()

            # fetch image and attach
            post_img_url = f"https://picsum.photos/seed/post{random.randint(1,100000)}/1200/800"
            try:
                img_bytes = fetch_image_bytes(post_img_url)
                safe_save_image(post.image, f"{user.username}_post_{random.randint(1,10000)}.jpg", img_bytes)
            except Exception:
                # if image fails, continue with a blank or existing placeholder
                pass

            created_posts.append(post)

    print(f"✅ Created {len(created_posts)} posts.")

    # Friend linking (mutual)
    print("🤝 Creating friend relationships...")
    users_only = [u for u, p in created_users]
    for user in users_only:
        possible = [u for u in users_only if u != user]
        num_friends = random.randint(0, min(MAX_FRIENDS_PER_USER, len(possible)))
        chosen = random.sample(possible, num_friends)
        for friend in chosen:
            try:
                # use add() on M2M
                user.friends.add(friend)
                # if symmetrical=False on your model, also add reverse
                # but if symmetrical=True, adding once is enough
                # to be safe, attempt both
                try:
                    friend.friends.add(user)
                except Exception:
                    pass
            except Exception as e:
                print(f"⚠️ Couldn't add friend {friend} to {user}: {e}")

    print("✅ Friends created (random).")

    # Followers (optional): check if user has followers/followings attribute
    supports_followers = any(hasattr(User, attr) for attr in ("followers", "followings", "following"))
    if supports_followers:
        print("👀 Creating follower relationships (detected follower field)...")
        for user in users_only:
            others = [u for u in users_only if u != user]
            num_followers = random.randint(0, min(10, len(others)))
            chosen = random.sample(others, num_followers)
            for follower in chosen:
                try:
                    # prefer .followers.add(follower) if exists
                    if hasattr(user, "followers"):
                        user.followers.add(follower)
                    elif hasattr(user, "followings"):
                        user.followings.add(follower)
                    elif hasattr(user, "following"):
                        user.following.add(follower)
                except Exception as e:
                    print(f"⚠️ Couldn't add follower {follower} -> {user}: {e}")
        print("✅ Followers created.")
    else:
        print("ℹ️ No followers/followings field detected on User model; skipping followers creation.")

    # Random likes on posts
    print("❤️ Adding random likes to posts...")
    for post in created_posts:
        num_likes = random.randint(0, min(MAX_LIKES_PER_POST, len(users_only)))
        likers = random.sample(users_only, num_likes)
        for liker in likers:
            try:
                post.likes.add(liker)
                # create notification to post owner (if liker not owner)
                if post.user != liker:
                    create_notification_safe(sender=liker, receiver=post.user, message=f"{liker.username} liked your post", link=f"/post/{post.id}/")
            except Exception as e:
                print(f"⚠️ Couldn't add like by {liker} to post {post.id}: {e}")

    print("✅ Likes added.")

    # Random saved posts per user
    print("🔖 Saving random posts for users...")
    for user, _ in created_users:
        # choose up to MAX_SAVED_PER_USER random posts
        num_save = random.randint(0, min(MAX_SAVED_PER_USER, len(created_posts)))
        to_save = random.sample(created_posts, num_save)
        for p in to_save:
            try:
                user.saved_posts.add(p)
            except Exception as e:
                print(f"⚠️ Couldn't save post {p.id} for {user.username}: {e}")
    print("✅ Saved posts created.")

    # Random comments
    print("💬 Creating random comments on posts...")
    for post in created_posts:
        num_comments = random.randint(0, MAX_COMMENTS_PER_POST)
        commenters = random.choices(users_only, k=num_comments)
        for commenter in commenters:
            text = fake.sentence(nb_words=random.randint(3, 20))
            try:
                Comment.objects.create(post=post, user=commenter, text=text)
                if post.user != commenter:
                    create_notification_safe(sender=commenter, receiver=post.user, message=f"{commenter.username} commented on your post", link=f"/post/{post.id}/")
            except Exception as e:
                print(f"⚠️ Couldn't create comment by {commenter} on post {post.id}: {e}")

    print("✅ Comments created.")

    # Random chat messages between friend pairs
    print("✉️ Creating random chat messages between friends...")
    # Build pairs from friendships
    for user in users_only:
        # get friends queryset (if it's a manager)
        try:
            friends_qs = list(user.friends.all())
        except Exception:
            friends_qs = []
        for friend in friends_qs:
            # To avoid duplicating pairs twice, ensure lexical ordering
            if user.id >= friend.id:
                continue
            num_msgs = random.randint(0, MAX_MESSAGES_PER_PAIR)
            if num_msgs == 0:
                continue
            # simulate a conversation
            for _ in range(num_msgs):
                sender = random.choice([user, friend])
                receiver = friend if sender == user else user
                text = fake.sentence(nb_words=random.randint(1, 30))
                try:
                    Message.objects.create(sender=sender, receiver=receiver, text=text)
                    # notify receiver
                    create_notification_safe(sender=sender, receiver=receiver, message=f"{sender.username} sent you a message", link=f"/messages/?chat={sender.id}")
                except Exception as e:
                    print(f"⚠️ Couldn't create message {sender}->{receiver}: {e}")

    print("✅ Messages created.")

    print("🎉 Fake data generation complete!")
    print(f"➡️ Credentials: open {OUTPUT_FILE}")

if __name__ == "__main__":
    main()