import lcctoolkit.views as project_views
import lcctoolkit.mainapp.views as views

from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin

from django.conf import settings


OTHER_URLS = (static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) +
              static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))

handler500 = 'lcctoolkit.views.handler500'

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^login/', views.Login.as_view(), name='login'),
    url(r'^logout/', views.Logout.as_view()),
    url(r'^register/', views.Register.as_view(), name='register'),
    url(
        r'^reset/done/$',
        views.PasswordResetComplete.as_view(),
        name='password_reset_complete'
    ),
    url(
        (r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/'
         r'(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$'),
        views.PasswordResetConfirm.as_view(),
        name='password_reset_confirm'
    ),
    url(
        r'^approve/(?P<uidb64>[0-9A-Za-z_\-]+)$',
        views.ApproveRegistration.as_view(),
        name='approve',
    ),

    url(r'^crashme$', project_views.crashme, name='crashme'),

    url(r'^legislation/add/$', views.LegislationAdd.as_view()),
    url(r'^legislation/edit/.*$', views.LegislationEditView.as_view()),
    url(
        r'^legislation/add/articles.*$',
        views.AddArticles.as_view(),
        name="add_articles",
    ),
    url(
        r'^legislation/$',
        views.LegislationExplorer.as_view(),
        name="legislation",
    ),
    url(
        r'^legislation/(?P<legislation_pk>\d+)$',
        views.LegislationView.as_view(),
        name="legislation_details"
    ),
    url(r'^legislation/pages.*$', views.LegislationPagesView.as_view()),
    url(r'^legislation/articles/edit.*$', views.EditArticles.as_view()),
    url(r'^legislation/articles.*$', views.ArticlesList.as_view()),
    url(r'^$', views.Index.as_view()),
] + OTHER_URLS
