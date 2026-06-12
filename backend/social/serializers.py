from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Comment, Friendship, Like, Post

User = get_user_model()


class PublicUserSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "avatar"]


class FriendshipSerializer(serializers.ModelSerializer):
    requester_detail = PublicUserSerializer(source="requester", read_only=True)
    addressee_detail = PublicUserSerializer(source="addressee", read_only=True)

    class Meta:
        model = Friendship
        fields = [
            "id",
            "requester",
            "addressee",
            "requester_detail",
            "addressee_detail",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "status", "requester"]


class CommentSerializer(serializers.ModelSerializer):
    user_detail = PublicUserSerializer(source="user", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "post", "body", "user_detail", "created_at"]
        read_only_fields = ["created_at", "user_detail"]


class PostSerializer(serializers.ModelSerializer):
    user_detail = PublicUserSerializer(source="user", read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    likes_count = serializers.IntegerField(source="likes.count", read_only=True)
    liked_by_me = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "body",
            "workout",
            "image",
            "user_detail",
            "comments",
            "likes_count",
            "liked_by_me",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "user_detail", "likes_count", "liked_by_me"]

    def get_liked_by_me(self, obj):
        user = self.context["request"].user
        return Like.objects.filter(post=obj, user=user).exists()
