from django.conf.urls import url, include
from django.contrib import admin
from controlcenter.views import controlcenter

urlpatterns = [
    url(r'^admin/dashboard/', controlcenter.urls),
    url(r'^', include('appserver_rest.urls')),
    url(r'^admin/', admin.site.urls),
]

