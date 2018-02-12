from django.conf.urls import url, include
from django.contrib import admin
from controlcenter.views import controlcenter
from . import views

urlpatterns = [
    url(r'^chart/pie/', views.pie_data, name='pie_data'),
    url(r'^chart/line/ctr/', views.line_ctr_data, name='line_ctr_data'),
    url(r'^chart/line/time/', views.line_time_data, name='line_time_data'),
    url(r'^admin/dashboard/', controlcenter.urls),
    url(r'^', include('appserver_rest.urls')),
    url(r'^admin/', admin.site.urls),
]