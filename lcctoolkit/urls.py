import lcctoolkit.mainapp.views as views

from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin

from django.conf import settings


OTHER_URLS = (static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) +
              static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^login/', views.Login.as_view()),
    url(r'^logout/', views.Logout.as_view()),
    url(r'^legislation/add/$', views.LegislationAdd.as_view()),
    url(r'^legislation/edit/.*', views.LegislationEditView.as_view()),
    url(r'^legislation/add/articles.*$', views.LegislationManagerArticles.as_view(), name="add_articles"),
    url(r'^legislation/$', views.LegislationExplorer.as_view(), name="legislation"),
    url(r'^legislation/(?P<legislation_pk>\d+)$', views.LegislationView.as_view(), name="legislation_details"),
    url(r'^legislation/pages.*$', views.LegislationPagesView.as_view()),
    url(r'^$', views.Index.as_view()),
] + OTHER_URLS
