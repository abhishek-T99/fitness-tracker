from rest_framework.routers import DefaultRouter

from .views import FriendshipViewSet, PostViewSet, UserSearchViewSet

router = DefaultRouter()
router.register("friendships", FriendshipViewSet, basename="friendship")
router.register("users", UserSearchViewSet, basename="user-search")
router.register("posts", PostViewSet, basename="post")

urlpatterns = router.urls
