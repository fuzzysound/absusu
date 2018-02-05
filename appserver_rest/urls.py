### url과 view를 연결해주는 파일
from django.conf.urls import url, include
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter() # 일반적인 방식으로 url을 자동으로 지정해주는 router
router.register(r'useractions', UserActionViewSet)
router.register(r'userassignments', UserAssignmentViewSet)


urlpatterns = [
    url(r'^', include(router.urls)), # router 적용
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')) # 관리자 로그인 기능 추가
]