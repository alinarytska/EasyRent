from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.users.models import User
from apps.users.serializers import UserSerializer


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSerializer

    def get_queryset(self):
        queryset = User.objects.all()
        user = self.request.user

        if not user.is_authenticated:
            return queryset.none()

        if user.is_staff:
            return queryset

        return queryset.filter(pk=user.pk)

    @action(detail=False, methods=("get",), url_path="me")
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
