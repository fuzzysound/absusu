from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from .views import *

urlpatterns = [
    url(r'^useractions/$', UserActionList.as_view()),
    url(r'^useractions/(?P<pk>[0-9]+)/$', UserActionDetail.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)