from rest_framework import viewsets

from apps.search_history.models import SearchHistory
from apps.search_history.serializers import SearchHistorySerializer


class SearchHistoryViewSet(viewsets.ModelViewSet):
    serializer_class = SearchHistorySerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return SearchHistory.objects.none()

        return SearchHistory.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
