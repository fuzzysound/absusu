from django.conf.urls import url, include
from django.contrib import admin
from controlcenter.views import controlcenter
from . import views

urlpatterns = [
    url(r'^chart/pie/', views.piedata, name='pie_data'),
    url(r'^chart/line/', views.linedata, name='line_data'),
    url(r'^admin/dashboard/', controlcenter.urls),
    url(r'^', include('appserver_rest.urls')),
    url(r'^admin/', admin.site.urls),
]