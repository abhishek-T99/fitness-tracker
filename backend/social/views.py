from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from .models import Comment, Friendship, Like, Post
from .serializers import (
    CommentSerializer,
    FriendshipSerializer,
    PostSerializer,
    PublicUserSerializer,
)

User = get_user_model()


class FriendshipViewSet(viewsets.ModelViewSet):
    serializer_class = FriendshipSerializer

    def get_queryset(self):
        return Friendship.objects.filter(
            Q(requester=self.request.user) | Q(addressee=self.request.user)
        )

    def create(self, request, *args, **kwargs):
        addressee_id = request.data.get("addressee")
        if not addressee_id:
            raise ValidationError({"addressee": "This field is required."})
        if int(addressee_id) == request.user.id:
            raise ValidationError("Cannot friend yourself.")
        existing = Friendship.objects.filter(
            Q(requester=request.user, addressee_id=addressee_id)
            | Q(requester_id=addressee_id, addressee=request.user)
        ).first()
        if existing:
            return Response(FriendshipSerializer(existing).data, status=status.HTTP_200_OK)
        friendship = Friendship.objects.create(
            requester=request.user, addressee_id=addressee_id
        )
        return Response(FriendshipSerializer(friendship).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        f = self.get_object()
        if f.addressee != request.user:
            raise PermissionDenied("Only the addressee can accept.")
        f.status = Friendship.Status.ACCEPTED
        f.save()
        return Response(FriendshipSerializer(f).data)

    @action(detail=True, methods=["post"])
    def decline(self, request, pk=None):
        f = self.get_object()
        if f.addressee != request.user:
            raise PermissionDenied("Only the addressee can decline.")
        f.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"])
    def friends(self, request):
        accepted = Friendship.objects.filter(
            status=Friendship.Status.ACCEPTED
        ).filter(Q(requester=request.user) | Q(addressee=request.user))
        friend_users = []
        for f in accepted:
            other = f.addressee if f.requester == request.user else f.requester
            friend_users.append(other)
        return Response(PublicUserSerializer(friend_users, many=True).data)


class UserSearchViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PublicUserSerializer
    search_fields = ["username", "first_name", "last_name"]

    def get_queryset(self):
        return User.objects.exclude(id=self.request.user.id)


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer

    def get_queryset(self):
        # Feed = my posts + posts from accepted friends.
        accepted = Friendship.objects.filter(
            status=Friendship.Status.ACCEPTED
        ).filter(Q(requester=self.request.user) | Q(addressee=self.request.user))
        friend_ids = set()
        for f in accepted:
            other = f.addressee_id if f.requester == self.request.user else f.requester_id
            friend_ids.add(other)
        friend_ids.add(self.request.user.id)
        return (
            Post.objects.filter(user_id__in=friend_ids)
            .select_related("user", "workout")
            .prefetch_related("comments__user", "likes")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def like(self, request, pk=None):
        post = self.get_object()
        like, created = Like.objects.get_or_create(post=post, user=request.user)
        if not created:
            like.delete()
            return Response({"liked": False, "likes_count": post.likes.count()})
        return Response({"liked": True, "likes_count": post.likes.count()})

    @action(detail=True, methods=["post"])
    def comment(self, request, pk=None):
        post = self.get_object()
        body = request.data.get("body", "").strip()
        if not body:
            raise ValidationError({"body": "This field is required."})
        comment = Comment.objects.create(post=post, user=request.user, body=body)
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)
