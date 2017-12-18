from django.http import HttpResponse
from rest_framework import status, generics
from rest_framework.response import Response
from .models import UserAction
from .serializers import UserActionSerializer

class UserActionList(generics.ListCreateAPIView):
    queryset = UserAction.objects.all()
    serializer_class = UserActionSerializer

class UserActionDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = UserAction.objects.all()
    serializer_class = UserActionSerializer