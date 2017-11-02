from django.conf.urls import url, include
from django.http import HttpResponseServerError, HttpResponse
from django.template import loader, TemplateDoesNotExist

from lcc import views
from lcc.context import sentry

auth_patterns = [
    url(r'^login/$',
        views.auth.Login.as_view(),
        name='login'),

    url(r'^logout/$',
        views.auth.Logout.as_view(),
        name='logout'),

    url(r'^register/',
        views.register.Register.as_view(),
        name='register'),

    url(r'^reset/done/$',
        views.register.PasswordResetComplete.as_view(),
        name='password_reset_complete'),

    url((r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/'
         r'(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$'),
        views.register.PasswordResetConfirm.as_view(),
        name='password_reset_confirm'),

    url(r'^approve/(?P<profile_id_b64>[0-9A-Za-z_\-]+)$',
        views.register.ApproveRegistration.as_view(),
        name='approve'),
]


article_patterns = [
    url(r'^add/$',
        views.articles.AddArticles.as_view(),
        name="add"),

    url(r'^$',
        views.articles.ArticlesList.as_view(),
        name='view'),

    url(r'^(?P<article_pk>\d+)/edit/$',
        views.articles.EditArticles.as_view(),
        name='edit'),

    url(r'^(?P<article_pk>\d+)/delete/$',
        views.articles.DeleteArticle.as_view(),
        name='delete'),
]

legislation_patterns = [
    url(r'^$',
        views.legislation.LegislationExplorer.as_view(),
        name="explorer"),

    url(r'^add/$',
        views.legislation.LegislationAdd.as_view(),
        name='add'),

    url(r'^(?P<legislation_pk>\d+)/$',
        views.legislation.LegislationView.as_view(),
        name="details"),

    url(r'^(?P<legislation_pk>\d+)/edit/$',
        views.legislation.LegislationEditView.as_view(),
        name='edit'),

    url(r'^(?P<legislation_pk>\d+)/delete/$',
        views.legislation.LegislationDeleteView.as_view(),
        name='delete'),

    url(r'^(?P<legislation_pk>\d+)/pages/$',
        views.legislation.LegislationPagesView.as_view()),

    url(r'^(?P<legislation_pk>\d+)/articles/',
        include(article_patterns, namespace='articles')),
]

country_patterns = [
    url(r'^(?P<iso>\w+)/$', views.country.Details.as_view(), name="view"),
    url(r'^(?P<iso>\w+)/customise$',
        views.country.Customise.as_view(),
        name="customise"),
]

api_urls = [
    url(r'question-category/(?P<category_pk>\d+).*$',
        views.api.QuestionViewSet.as_view(),
        name="question_category"),

    url(r'classification/$',
        views.api.ClassificationViewSet.as_view(),
        name="classification"),

    url(r'answers/$',
        views.api.AnswerList.as_view(),
        name='answers_list_create'),

    url(r'answers/(?P<pk>[0-9]+)/$',
        views.api.AnswerDetail.as_view(),
        name='answers_get_update'),

    url(r'assessments/$',
        views.api.AssessmentList.as_view(),
        name='assessment_list_create'),

    url(r'assessments/results/(?P<pk>[0-9]+)/$',
        views.api.AssessmentResults.as_view(),
        name='assessment_results'),

    url(r'countries/$',
        views.api.CountryViewSet.as_view(),
        name="countries")

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
        views.base.Index.as_view(),
        name='index'),

    url(r'^',
        include(auth_patterns, namespace='auth')),

    url(r'^api/',
        include(api_urls, namespace='api')),

    url(r'^crashme$', crash_me, name='crashme'),

    url(r'^legal-assessment/$',
        views.assessment.LegalAssessment.as_view(),
        name="legal_assessment"),

    url(r'^legislation/',
        include(legislation_patterns, namespace='legislation')),

    url(r'^country/',
        include(country_patterns, namespace='country')),

]
