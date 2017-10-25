from django.conf.urls import url, include
from django.http import HttpResponseServerError, HttpResponse
from django.template import loader, TemplateDoesNotExist

from lcc import views
from lcc.context import sentry

auth_patterns = [
    url(r'^login/$',
        views.Login.as_view(),
        name='login'),

    url(r'^logout/$',
        views.Logout.as_view(),
        name='logout'),

    url(r'^register/',
        views.Register.as_view(),
        name='register'),

    url(r'^reset/done/$',
        views.PasswordResetComplete.as_view(),
        name='password_reset_complete'),

    url((r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/'
         r'(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$'),
        views.PasswordResetConfirm.as_view(),
        name='password_reset_confirm'),

    url(r'^approve/(?P<profile_id_b64>[0-9A-Za-z_\-]+)$',
        views.ApproveRegistration.as_view(),
        name='approve'),
]


article_patterns = [
    url(r'^add/$',
        views.AddArticles.as_view(),
        name="add"),

    url(r'^$',
        views.ArticlesList.as_view(),
        name='view'),

    url(r'^(?P<article_pk>\d+)edit/$',
        views.EditArticles.as_view(),
        name='edit'),
]

legislation_patterns = [
    url(r'^$',
        views.LegislationExplorer.as_view(),
        name="explorer"),

    url(r'^add/$',
        views.LegislationAdd.as_view(),
        name='add'),

    url(r'^(?P<legislation_pk>\d+)/$',
        views.LegislationView.as_view(),
        name="details"),

    url(r'^(?P<legislation_pk>\d+)/edit/$',
        views.LegislationEditView.as_view(),
        name='edit'),

    url(r'^(?P<legislation_pk>\d+)/pages/$',
        views.LegislationPagesView.as_view()),

    url(r'^(?P<legislation_pk>\d+)/articles/',
        include(article_patterns, namespace='articles')),
]

api_urls = [
    url(r'question-category/(?P<category_pk>\d+)/$',
        views.QuestionViewSet.as_view(),
        name="question_category"),

    url(r'classification/$',
        views.ClassificationViewSet.as_view(),
        name="classification"),

    url(r'answers/$',
        views.AnswerList.as_view(),
        name='answers_list_create'),

    url(r'answers/(?P<pk>[0-9]+)/$',
        views.AnswerDetail.as_view(),
        name='answers_get_update')
]


def handler500(request, template_name='errors/500.html'):
    try:
        template = loader.get_template(template_name)
    except TemplateDoesNotExist:
        return HttpResponseServerError('<h1>Server Error (500)</h1>',
                                       content_type='text/html')
    return HttpResponseServerError(template.render(context=sentry(request)))


def crash_me(request):
    if request.user.is_superuser:
        raise RuntimeError("Crashing as requested")
    else:
        return HttpResponse("Must be administrator")


urlpatterns = [
    url(r'^$',
        views.Index.as_view(),
        name='index'),

    url(r'^',
        include(auth_patterns, namespace='auth')),

    url(r'^api/',
        include(api_urls, namespace='api')),

    url(r'^crashme$', crash_me, name='crashme'),

    url(r'^legal-assessment/$',
        views.LegalAssessment.as_view(),
        name="legal_assessment"),

    url(r'^legislation/',
        include(legislation_patterns, namespace='legislation')),
]
