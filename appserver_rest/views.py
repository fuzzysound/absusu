### 페이지에 데이터를 어떻게 나타낼지 정의하는 파일
from rest_framework import viewsets
from .models import UserAction, UserAssignment
from .serializers import UserActionSerializer, UserAssignmentSerializer


class UserActionViewSet(viewsets.ModelViewSet): # UserAction 모델의 viewset
    queryset = UserAction.objects.all()
    serializer_class = UserActionSerializer

class UserAssignmentViewSet(viewsets.ModelViewSet): # UserAssignment 모델의 viewset
    queryset = UserAssignment.objects.all()
    serializer_class = UserAssignmentSerializer