### 페이지에 데이터를 어떻게 나타낼지 정의하는 파일
from rest_framework import viewsets
from rest_framework.renderers import AdminRenderer, JSONRenderer
# AdminRenderer는 테이블 형식(보기 편한 형태), JSONRenderer는 JSON 형식(JSON 형식으로 response를 보내기 위한 것)
# (JSON 형식으로 response를 받기 위해서는 request의 header에 {"Accept":"application/json"}이 포함되어 있어야 함.
from .models import UserAction, UserAssignment
from .serializers import UserActionSerializer, UserAssignmentSerializer


class UserActionViewSet(viewsets.ModelViewSet): # UserAction 모델의 viewset
    queryset = UserAction.objects.all()
    serializer_class = UserActionSerializer
    renderer_classes = (AdminRenderer, JSONRenderer, ) # 두 개의 renderer를 제공한다

class UserAssignmentViewSet(viewsets.ModelViewSet): # UserAssignment 모델의 viewset
    queryset = UserAssignment.objects.all()
    serializer_class = UserAssignmentSerializer
    renderer_classes = (AdminRenderer, JSONRenderer, ) # UserAction과 마찬가지로 두 개의 renderer 제공