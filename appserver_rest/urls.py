from django.conf.urls import url
from .views import *

urlpatterns = [
    url(r'^useractions/$', UserActionList.as_view()),
    url(r'^useractions/(?P<pk>[0-9]+)/$', UserActionDetail.as_view()),
]

