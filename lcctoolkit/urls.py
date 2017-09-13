import lcctoolkit.mainapp.views as views

from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin

from django.conf import settings


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^login/',views.login),
    url(r'^logout/', views.logout),
    url(r'^$', views.index),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


