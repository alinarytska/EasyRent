from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.view_history.models import ViewHistory
from apps.view_history.serializers import ViewHistorySerializer


class ViewHistoryViewSet(viewsets.ModelViewSet):
    serializer_class = ViewHistorySerializer

    def get_queryset(self):
        queryset = ViewHistory.objects.select_related("user", "listing")

        if not self.request.user.is_authenticated:
            return queryset.none()

        return queryset.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        view_history, created = ViewHistory.objects.update_or_create(
            user=request.user,
            listing=serializer.validated_data["listing"],
            defaults={},
        )
        response_serializer = self.get_serializer(view_history)
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK

        return Response(response_serializer.data, status=response_status)
