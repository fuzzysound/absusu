""" A/B Test Platform Project with SKTelecom and SKBroadband

Authors: Junhyun Koh, Won Kim, Yonghoon Jeon at Big Data Institute, Seoul National University

File: absusu/absusu/urls.py
"""
from django.conf.urls import url, include
from controlcenter.views import controlcenter
from . import views
from experimenter.admin import absusu_admin

urlpatterns = [
    url(r'^chart/pie/', views.pie_data, name='pie_data'),
    url(r'^chart/line/ctr/', views.line_ctr_data, name='line_ctr_data'),
    url(r'^chart/line/time/', views.line_time_data, name='line_time_data'),
    url(r'^admin/', include(absusu_admin.urls)),
    url(r'^admin/dashboard/', controlcenter.urls),
    url(r'^', include('appserver_rest.urls')),
]