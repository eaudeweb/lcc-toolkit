from django.conf import settings
from django.urls import path, include, re_path
from django.contrib.auth.decorators import permission_required, login_required
from django.http import HttpResponseServerError, HttpResponse
from django.template import loader, TemplateDoesNotExist
from django.views.static import serve


from lcc import views
from lcc.context import sentry
from lcc.utils import login_forbidden


app_name = "lcc"


auth_patterns = [
    path("login/", login_forbidden(views.auth.Login.as_view()), name="login"),
    path("logout/", views.auth.Logout.as_view(), name="logout"),
    path(
        "register/", login_forbidden(views.register.Register.as_view()), name="register"
    ),
    path(
        "reset/done/",
        views.register.PasswordResetComplete.as_view(),
        name="password_reset_complete",
    ),
    re_path(
        (
            r"^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/"
            r"(?P<token>[0-9A-Za-z]{1,25}-[0-9A-Za-z]{1,40})/"
        ),
        views.register.PasswordResetConfirm.as_view(),
        name="password_reset_confirm",
    ),
    re_path(
        r"^approve/(?P<profile_id_b64>[0-9A-Za-z_\-]+)",
        login_required(views.register.ApproveRegistration.as_view()),
        name="approve",
    ),
    path(
        "change-password/",
        views.auth.ChangePasswordView.as_view(),
        name="change_password",
    ),
    path(
        "password-reset/",
        login_forbidden(views.register.PasswordResetView.as_view()),
        name="password_reset",
    ),
]


section_patterns = [
    path(
        "add/",
        permission_required("lcc.add_legislationsection")(
            views.sections.AddSections.as_view()
        ),
        name="add",
    ),
    path("", views.sections.SectionsList.as_view(), name="view"),
    path(
        "<int:section_pk>/edit/",
        permission_required("lcc.change_legislationsection")(
            views.sections.EditSections.as_view()
        ),
        name="edit",
    ),
    path(
        "<int:section_pk>/delete/",
        permission_required("lcc.delete_legislationsection")(
            views.sections.DeleteSection.as_view()
        ),
        name="delete",
    ),
]

legislation_patterns = [
    path("", views.legislation.LegislationExplorer.as_view(), name="explorer"),
    path(
        "add/",
        permission_required("lcc.add_legislation")(
            views.legislation.LegislationAdd.as_view()
        ),
        name="add",
    ),
    path(
        "<int:legislation_pk>/",
        views.legislation.LegislationView.as_view(),
        name="details",
    ),
    path(
        "<int:legislation_pk>/edit/",
        permission_required("lcc.change_legislation")(
            views.legislation.LegislationEditView.as_view()
        ),
        name="edit",
    ),
    path(
        "<int:legislation_pk>/delete/",
        permission_required("lcc.delete_legislation")(
            views.legislation.LegislationDeleteView.as_view()
        ),
        name="delete",
    ),
    path(
        "<int:legislation_pk>/pages/", views.legislation.LegislationPagesView.as_view()
    ),
    path(
        "<int:legislation_pk>/articles/",
        include((section_patterns, app_name), namespace="sections"),
    ),
]

country_patterns = [
    path("<str:iso>/", views.country.Details.as_view(), name="view"),
    path(
        "<str:iso>/delete",
        views.country.DeleteCustomisedProfile.as_view(),
        name="delete",
    ),
    path("<str:iso>/customise", views.country.Customise.as_view(), name="customise"),
]

api_patterns = [
    re_path(
        r"^question-category/(?P<category_pk>\d+).*",
        views.api.QuestionViewSet.as_view(),
        name="question_category",
    ),
    path(
        "classification/",
        views.api.ClassificationViewSet.as_view(),
        name="classification",
    ),
    path("answers/", views.api.AnswerList.as_view(), name="answers_list_create"),
    path(
        "answers/<int:pk>/", views.api.AnswerDetail.as_view(), name="answers_get_update"
    ),
    path(
        "assessments/",
        views.api.AssessmentList.as_view(),
        name="assessment_list_create",
    ),
    path(
        "assessments/<int:pk>/results/",
        views.api.AssessmentResults.as_view(),
        name="assessment_results",
    ),
    path("countries/", views.api.CountryViewSet.as_view(), name="countries"),
]

assessment_patterns = [
    path("", views.assessment.LegalAssessment.as_view(), name="legal_assessment"),
    path(
        "<int:pk>/results/",
        views.assessment.LegalAssessmentResults.as_view(),
        name="legal_assessment_results",
    ),
    path(
        "<int:pk>/results/download",
        views.assessment.LegalAssessmentResultsPDF.as_view(),
        name="legal_assessment_results_pdf",
    ),
]


def handler500(request, template_name="errors/500.html"):
    try:
        template = loader.get_template(template_name)
    except TemplateDoesNotExist:
        return HttpResponseServerError(
            "<h1>Server Error (500)</h1>", content_type="text/html"
        )
    return HttpResponseServerError(template.render(context=sentry(request)))


def crash_me(request):
    if request.user.is_superuser:
        raise RuntimeError("Crashing as requested")
    else:
        return HttpResponse("Must be administrator")


urlpatterns = [
    path("", views.base.HomePageView.as_view(), name="home_page"),
    path("about-us/", views.base.AboutUsView.as_view(), name="about_us"),
    path("", include((auth_patterns, app_name), namespace="auth")),
    path("api/", include((api_patterns, app_name), namespace="api")),
    path("crashme/", crash_me, name="crashme"),
    path(
        "legal-assessment/",
        include((assessment_patterns, app_name), namespace="assessment"),
    ),
    path(
        "legislation/",
        include((legislation_patterns, app_name), namespace="legislation"),
    ),
    path("country/", include((country_patterns, app_name), namespace="country")),
    path("docs/<path:path>/", serve, {"document_root": settings.DOCS_ROOT}),
    path(
        "docs/guide.html",
        serve,
        {"document_root": settings.DOCS_ROOT},
        name="user_manual",
    ),
]
