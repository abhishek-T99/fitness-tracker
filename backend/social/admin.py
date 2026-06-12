from django.contrib import admin

from .models import Comment, Friendship, Like, Post


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ("requester", "addressee", "status", "created_at")
    list_filter = ("status",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "workout")
    search_fields = ("body", "user__username")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("post", "user", "created_at")


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("post", "user", "created_at")
