from rest_framework.generics import ListAPIView

from apps.documents.models import Document
from apps.documents.serializers import DocumentSerializer


class DocumentListAPIView(ListAPIView):
    serializer_class = DocumentSerializer

    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)
