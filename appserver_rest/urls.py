from django.conf.urls import url, include
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'useractions', UserActionViewSet)


urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]

