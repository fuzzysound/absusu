from rest_framework import status, generics, viewsets
from .models import UserAction
from .serializers import UserActionSerializer

class UserActionList(generics.ListCreateAPIView):
    queryset = UserAction.objects.all()
    serializer_class = UserActionSerializer

class UserActionDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = UserAction.objects.all()
    serializer_class = UserActionSerializer

class UserActionViewSet(viewsets.ModelViewSet):
    queryset = UserAction.objects.all()
    serializer_class = UserActionSerializer