from django.contrib import admin
from django.utils.html import format_html

from .models import Comment, Friendship, Like, Post


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ("requester", "addressee", "status_badge", "created_at")
    list_filter = ("status",)
    search_fields = ("requester__username", "addressee__username")
    autocomplete_fields = ("requester", "addressee")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    @admin.display(description="Status")
    def status_badge(self, obj):
        colours = {
            "pending": ("#f59e0b", "#fff"),
            "accepted": ("#10b981", "#fff"),
            "declined": ("#ef4444", "#fff"),
        }
        bg, fg = colours.get(obj.status, ("#94a3b8", "#fff"))
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;'
            'border-radius:9999px;font-size:11px;font-weight:600;">{}</span>',
            bg, fg, obj.get_status_display(),
        )


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("user", "body_preview", "workout", "like_count", "comment_count", "created_at")
    search_fields = ("body", "user__username")
    autocomplete_fields = ("user",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    readonly_fields = ("like_count", "comment_count")

    @admin.display(description="Preview")
    def body_preview(self, obj):
        return (obj.body or "")[:60] + ("…" if len(obj.body or "") > 60 else "")

    @admin.display(description="Likes")
    def like_count(self, obj):
        return obj.likes.count()

    @admin.display(description="Comments")
    def comment_count(self, obj):
        return obj.comments.count()


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("user", "body_preview", "post", "created_at")
    search_fields = ("body", "user__username")
    autocomplete_fields = ("user", "post")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    @admin.display(description="Comment")
    def body_preview(self, obj):
        return (obj.body or "")[:60] + ("…" if len(obj.body or "") > 60 else "")


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("user", "post", "created_at")
    autocomplete_fields = ("user",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
