from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin

from django.conf import settings


urlpatterns = (
    [
        url(r"^admin/", admin.site.urls),
        url(r"^", include("lcc.urls", namespace="lcc")),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)
