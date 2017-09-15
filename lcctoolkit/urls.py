import lcctoolkit.mainapp.views as views

from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin

from django.conf import settings


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^login/',views.Login.as_view()),
    url(r'^logout/', views.Logout.as_view()),
    url(r'^$', views.Index.as_view()),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


