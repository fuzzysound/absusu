from rest_framework import viewsets
from .models import UserAction
from .serializers import UserActionSerializer

class UserActionViewSet(viewsets.ModelViewSet):
    queryset = UserAction.objects.all()
    serializer_class = UserActionSerializer

