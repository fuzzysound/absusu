""" A/B Test Platform Project with SKTelecom and SKBroadband

Authors: Junhyun Koh, Won Kim, Yonghoon Jeon at Big Data Institute, Seoul National University

File: absusu/appserver_rest/urls.py
"""
"""
url과 view를 연결해주는 파일
"""
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter() # 일반적인 방식으로 url을 자동으로 지정해주는 router
router.register(r'useractions', UserActionViewSet)
router.register(r'userassignments', UserAssignmentViewSet)


urlpatterns = [
    url(r'^', include(router.urls)), # router 적용
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')) # 관리자 로그인 기능 추가
]