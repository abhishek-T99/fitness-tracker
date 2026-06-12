from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import (
    TokenObtainPairView as _TokenObtainPairView,
    TokenRefreshView as _TokenRefreshView,
)
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    ChangePasswordSerializer,
    RegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

User = get_user_model()


def tokens_for(user):
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


# Thin wrappers so we can attach tags without mutating the library classes.
# authentication_classes=[] is intentional: these are public endpoints and must
# not run JWT auth. A stale token in the browser would otherwise cause
# JWTAuthentication to raise AuthenticationFailed before AllowAny can permit
# the request, blocking login/register for users with old sessions.
@extend_schema(tags=["Auth"], auth=[])
class TokenObtainPairView(_TokenObtainPairView):
    authentication_classes = []


@extend_schema(tags=["Auth"], auth=[])
class TokenRefreshView(_TokenRefreshView):
    authentication_classes = []


@extend_schema(
    tags=["Auth"],
    auth=[],
    request=RegisterSerializer,
    responses={
        201: inline_serializer(
            name="RegisterResponse",
            fields={
                "user": UserSerializer(),
                "tokens": inline_serializer(
                    name="TokenPair",
                    fields={
                        "access": serializers.CharField(),
                        "refresh": serializers.CharField(),
                    },
                ),
            },
        ),
    },
)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"user": UserSerializer(user).data, "tokens": tokens_for(user)},
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    get=extend_schema(tags=["Auth"], responses=UserSerializer),
    put=extend_schema(tags=["Auth"], request=UserUpdateSerializer, responses=UserSerializer),
    patch=extend_schema(tags=["Auth"], request=UserUpdateSerializer, responses=UserSerializer),
)
class MeView(generics.RetrieveUpdateAPIView):
    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserUpdateSerializer
        return UserSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(UserSerializer(instance).data)


@extend_schema(
    tags=["Auth"],
    request=ChangePasswordSerializer,
    responses={
        200: inline_serializer(
            name="ChangePasswordResponse",
            fields={"detail": serializers.CharField()},
        ),
        400: inline_serializer(
            name="ChangePasswordError",
            fields={"old_password": serializers.CharField()},
        ),
    },
)
class ChangePasswordView(APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"old_password": "Incorrect password."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response({"detail": "Password updated."})
