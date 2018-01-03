from rest_framework import viewsets
from .models import UserAction, UserAssignment
from .serializers import UserActionSerializer, UserAssignSerializer


class UserActionViewSet(viewsets.ModelViewSet):
    queryset = UserAction.objects.all()
    serializer_class = UserActionSerializer

class UserAssignViewSet(viewsets.ModelViewSet):
    queryset = UserAssignment.objects.all()
    serializer_class = UserAssignSerializer