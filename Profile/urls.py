from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout, name='logout'),
    path('create/post/', views.create_post, name='create_post'),
    path('save/<int:post_id>/', views.save_post, name='save_post'),
    path('post/<int:post_id>/', views.view_post, name='view_post'),
    path('edit/<int:post_id>/', views.edit_post, name='edit_post'),
    path('delete/<int:post_id>/', views.delete_post, name='delete_post'),
    path('post/<int:post_id>/like/', views.like_post, name='toggle_like'),
    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('saved_posts/', views.saved_posts, name='saved_posts'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('profile/', views.profile, name='profile'),
    path('profile/<int:user_id>/', views.view_profile, name='view_profile'),
    path('profile/<int:user_id>/friends/', views.view_friends, name='view_friends'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('friend/<int:user_id>/', views.friend, name='friend'),
    path('unfriend/<int:user_id>/', views.unfriend, name='unfriend'),
    path('search/', views.search_user, name='search_user'),
    path('notifications/', views.notifications, name='notifications'),
    path('messages/', views.messages_page, name='messages_page'),
    path('messages/send/<int:receiver_id>/', views.send_message, name='send_message'),
]