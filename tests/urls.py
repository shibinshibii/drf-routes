from django.urls import path, include
from rest_framework import serializers, viewsets, routers
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse


# ── Serializers ──────────────────────────────────────────────────────────────

class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class PostSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()


# ── ViewSets ─────────────────────────────────────────────────────────────────

class UserViewSet(viewsets.ViewSet):
    serializer_class = UserSerializer

    def list(self, request):
        return Response([])

    def retrieve(self, request, pk=None):
        return Response({})

    def create(self, request):
        return Response({})

    def update(self, request, pk=None):
        return Response({})

    def destroy(self, request, pk=None):
        return Response({})


class PostViewSet(viewsets.ViewSet):
    serializer_class = PostSerializer

    def list(self, request):
        return Response([])

    def create(self, request):
        return Response({})


# ── APIViews ─────────────────────────────────────────────────────────────────

class LoginView(APIView):
    def post(self, request):
        return Response({"token": "abc"})


class MeView(APIView):
    serializer_class = UserSerializer

    def get(self, request):
        return Response({})

    def patch(self, request):
        return Response({})


# ── Plain Django view ─────────────────────────────────────────────────────────

def health_check(request):
    return HttpResponse("ok")


# ── Router ───────────────────────────────────────────────────────────────────

router = routers.DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"posts", PostViewSet, basename="post")


# ── URL patterns ─────────────────────────────────────────────────────────────

urlpatterns = [
    path("api/", include(router.urls)),
    path("api/auth/login/", LoginView.as_view(), name="auth-login"),
    path("api/auth/me/",    MeView.as_view(),    name="auth-me"),
    path("health/",         health_check,         name="health-check"),
]