import json
import pdftotext
import re
import time
from functools import partial

import django.db
from django.db import transaction
from django.db.models import Q

import django.contrib.auth as auth
import django.contrib.auth.mixins as mixins
import django.core as core

from django.contrib.auth.models import User
from django.core.mail import send_mail

from django.template.loader import get_template
import django.shortcuts
import django.http
import django.views as views

from rolepermissions.roles import RolesManager

import lcctoolkit.mainapp.constants as constants
import lcctoolkit.mainapp.models as models
import lcctoolkit.settings as settings
import lcctoolkit.roles as roles


LEGISLATION_YEAR_RANGE = range(1945, constants.LEGISLATION_DEFAULT_YEAR + 1)


def selected_taxonomy(request, is_tags=False):
    selector = "classification"
    if is_tags:
        selector = "tag"
    selected_ids = [int(el.split('_')[1])
                    for el in request.POST.keys()
                    if el.startswith(selector + "_")]
    if is_tags:
        return models.TaxonomyTag.objects.filter(pk__in=selected_ids)
    else:
        return models.TaxonomyClassification.objects.filter(
            pk__in=selected_ids)


def taxonomy_to_string(legislation, tags=False, classification=False):

    if tags:
        return ", ".join(list(legislation.tags.values_list('name', flat=True)))

    if classification:
        return ", ".join(
            list(legislation.classifications.values_list('name', flat=True))
        )


def response_error(request, errors, template="message.html"):

    return django.shortcuts.render(request, template, {"errors": errors})


class UserPatchMixin():

    def dispatch(self, request, *args, **kwargs):
        self.user_profile = None
        if request.user.is_authenticated:
            self.user_profile = models.UserProfile.objects.get(
                user=request.user
            )
            request.user_profile = self.user_profile
        return super(UserPatchMixin, self).dispatch(request, *args, **kwargs)


class Index(UserPatchMixin, views.View):

    def get(self, request):
        return django.http.HttpResponseRedirect("/legislation/")


class Login(views.View):

    template = "login.html"

    def get(self, request):
        return django.shortcuts.render(request, self.template)

    def post(self, request):
        user = auth.authenticate(
            request,
            username=request.POST[constants.POST_DATA_USERNAME_KEY],
            password=request.POST[constants.POST_DATA_PASSWORD_KEY]
        )
        if user:
            auth.login(request, user)
            return django.http.HttpResponse(
                json.dumps({'msg': constants.AJAX_RETURN_SUCCESS}))
        else:
            return django.http.HttpResponse(
                json.dumps({'msg': constants.AJAX_RETURN_FAILURE}))


class Logout(views.View):

    def get(self, request):
        auth.logout(request)
        return django.http.HttpResponseRedirect("/")


class LegislationExplorer(UserPatchMixin, views.View):

    template = "legislation.html"

    def get(self, request):
        laws = models.Legislation.objects.all()
        group_tags = models.TaxonomyTagGroup.objects.all()
        top_classifications = models.TaxonomyClassification.objects \
            .filter(level=0).order_by('code')
        countries = models.Country.objects.all()

        req_dict = dict(request.GET)
        # @TODO add filter for YEAR and LANGUAGE
        if bool(req_dict):
            if req_dict.get('tags[]'):
                for tag in req_dict['tags[]']:
                    laws = laws.filter(tags=tag)

            if req_dict.get('classification[]'):
                for classification in req_dict['classification[]']:
                    laws = laws.filter(classifications=classification)

            if req_dict.get('country'):
                laws = laws.filter(country__iso=req_dict.get('country')[0])

            if req_dict.get('type'):
                laws = laws.filter(law_type=req_dict.get('type')[0])

        laws = laws.order_by('-pk')

        # For now, tags and classifications are displayed as a string
        # @TODO find a better approach
        for law in laws:
            law.all_tags = taxonomy_to_string(law, tags=True)
            law.all_classifications = taxonomy_to_string(
                law, classification=True
            )

        legislation_year = (
            LEGISLATION_YEAR_RANGE[0],
            LEGISLATION_YEAR_RANGE[len(LEGISLATION_YEAR_RANGE) - 1]
        )

        context = {
            'laws': laws,
            'group_tags': group_tags,
            'top_classifications': top_classifications,
            'countries': countries,
            'legislation_type': constants.LEGISLATION_TYPE,
            'legislation_year': legislation_year
        }

        return django.shortcuts.render(request, self.template, context)


class LegislationAdd(UserPatchMixin, mixins.LoginRequiredMixin, views.View):

    login_url = constants.LOGIN_URL
    template = "legislationAdd.html"
    taxonomy_classifications = models.TaxonomyClassification.\
        objects.filter(level=0).order_by('code')

    def legislation_form_check_year_details(year_details, errors):
        years_in_year_details = [
            int(year)
            for year in re.findall('\d\d\d\d', year_details)
        ]

        if years_in_year_details:
            if not any(year in LEGISLATION_YEAR_RANGE
                       for year in years_in_year_details):
                errors["year_details"] = "Please add a year in %d-%d range" % (
                    LEGISLATION_YEAR_RANGE[0], LEGISLATION_YEAR_RANGE[-1]
                )
        else:
            errors["year_details"] = (
                "'Additional date details' field needs a 4 digit year."
            )

    def legislation_form_get_pdf_file(file, errors):
        try:
            return pdftotext.PDF(file)
        except pdftotext.Error:
            errors["pdf"] = "The .pdf file is corrupted. Please reupload it."

    def legislation_form_check_website(website, errors):
        url = core.validators.URLValidator()
        try:
            url(website)
        except core.exceptions.ValidationError:
            errors["website"] = "Please enter a valid website."

    def legislation_save_pdf_pages(law, pdf):
        if settings.DEBUG:
            time_to_load_pdf = time.time()
        if settings.DEBUG:
            print("INFO: FS pdf file load time: %fs" %
                  (time.time() - time_to_load_pdf))
            time_begin_transaction = time.time()

        with django.db.transaction.atomic():
            for idx, page in enumerate(pdf):
                page = page.replace('\x00', '')
                models.LegislationPage(
                    page_text="<pre>%s</pre>" % page,
                    page_number=idx + 1,
                    legislation=law
                ).save()

        if settings.DEBUG:
            print("INFO: ORM models.LegislationPages save time: %fs" %
                  (time.time() - time_begin_transaction))

    class TagGroupRender():

        def __init__(self, tag_group):
            self.name = tag_group.name
            self.pk = tag_group.pk
            self.tags = [{'name': tag.name, 'pk': tag.pk}
                         for tag in models.TaxonomyTag.objects.filter(
                group=tag_group)]

    def get(self, request):
        countries = sorted(models.Country.objects.all(), key=lambda c: c.name)
        return django.shortcuts.render(request, self.template, {
            "countries": countries,
            "user_country": request.user_profile.country,
            "legislation_type": constants.LEGISLATION_TYPE,
            "tag_groups": [
                LegislationAdd.TagGroupRender(tag_group)
                for tag_group in models.TaxonomyTagGroup.objects.all()
            ],
            "classifications": LegislationAdd.taxonomy_classifications,
            "available_languages": constants.ALL_LANGUAGES,
            "source_types": constants.SOURCE_TYPE,
            "geo_coverage": constants.GEOGRAPHICAL_COVERAGE,
            "adoption_years": LEGISLATION_YEAR_RANGE,
            "classifications": LegislationAdd.taxonomy_classifications
        })

    def post(self, request):

        title = request.POST["title"]
        abstract = request.POST["abstract"]
        uploaded_file = request.FILES['pdf_file']

        country = models.Country.objects.filter(
            iso=request.POST["country"])[0]
        language = request.POST["language"]
        law_type = request.POST["law_type"]
        geo_coverage = request.POST["geo"]

        website = request.POST["website"]
        source = request.POST["source"]
        source_type = request.POST["source_type"]

        year = int(request.POST["law_year"])
        amendment = int(request.POST["amendment_year"])
        year_details = request.POST["year_of_adoption_mention"]

        tags = [tag for tag in selected_taxonomy(request, is_tags=True)]
        classifications = [
            classification
            for classification in selected_taxonomy(request)
        ]

        # import ipdb; ipdb.set_trace()
        errors = {}
        self.legislation_form_check_year_details(year_details, errors)
        self.legislation_form_check_website(website, errors)
        pdf = self.legislation_form_get_pdf_file(uploaded_file, errors)

        if errors:
            return django.shortcuts.render(request, self.template, {
                "title": title,
                "abstract": abstract,

                "selected_country": country,
                "selected_language": language,
                "selected_law_type": law_type,
                "selected_geo": geo_coverage,

                "selected_website": website,
                "selected_source": source,
                "selected_source_type": source_type,

                "selected_year_of_adoption": year,
                "selected_year_of_amendment": amendment,
                "selected_year_details": year_details,

                "selected_tags": [tag.name for tag in tags],
                "selected_classifications": [
                    cl.name
                    for cl in classifications
                ],

                "countries": sorted(
                    models.Country.objects.all(),
                    key=lambda c: c.name
                ),
                "legislation_type": constants.LEGISLATION_TYPE,
                "tag_groups": [
                    LegislationAdd.TagGroupRender(tag_group)
                    for tag_group in models.TaxonomyTagGroup.objects.all()
                ],
                "available_languages": constants.ALL_LANGUAGES,
                "adoption_years": LEGISLATION_YEAR_RANGE,
                "classifications": LegislationAdd.taxonomy_classifications,
                "source_types": constants.SOURCE_TYPE,
                "geo_coverage": constants.GEOGRAPHICAL_COVERAGE,
                "errors": errors
            })

        law_obj = models.Legislation(
            title=title,
            abstract=abstract,
            country=country,
            language=language,
            law_type=law_type,
            year=year,
            year_amendment=amendment,
            year_mention=year_details,
            geo_coverage=geo_coverage,
            source=source,
            source_type=source_type,
            website=website,
            pdf_file_name=uploaded_file.name
        )

        law_obj.pdf_file.save(uploaded_file.name, uploaded_file.file)
        law_obj.save()

        for tag in tags:
            law_obj.tags.add(tag)
        for classification in classifications:
            law_obj.classifications.add(classification)

        self.legislation_save_pdf_pages(law_obj, pdf)

        if "save-and-continue-btn" in request.POST:
            return django.http.HttpResponseRedirect(
                "/legislation/add/articles?law_id=%s" % str(law_obj.pk)
            )
        if "save-btn" in request.POST:
            return django.http.HttpResponseRedirect("/legislation/")


class AddArticles(UserPatchMixin, mixins.LoginRequiredMixin, views.View):

    login_url = constants.LOGIN_URL
    template = "legislationManageArticles.html"

    def get(self, request):
        # WIP
        law = models.Legislation.objects.get(pk=request.GET.get("law_id"))
        if law.articles:
            last_article = law.articles.order_by('pk').last()
        else:
            last_article = None

        if last_article:
            starting_page = last_article.legislation_page
        else:
            starting_page = 1

        return django.shortcuts.render(request, self.template, {
            "law": law,
            "starting_page": starting_page,
            "last_article": last_article,
            "add_article": True,
            "tag_groups": [
                LegislationAdd.TagGroupRender(tag_group)
                for tag_group in models.TaxonomyTagGroup.objects.all()
            ],
            "classifications": LegislationAdd.taxonomy_classifications
        })

    def post(self, request):
        article_obj = models.LegislationArticle()
        law_id = request.POST.get("law_id")
        article_obj.code = request.POST.get("code")
        article_obj.text = request.POST.get("legislation_text")
        article_obj.legislation = models.Legislation.objects.get(
            pk=law_id)
        article_obj.legislation_page = request.POST.get("page")
        article_obj.save()

        for tag in selected_taxonomy(request, is_tags=True):
            article_obj.tags.add(tag)
        for classification in selected_taxonomy(request):
            article_obj.classifications.add(classification)

        if "save-and-continue-btn" in request.POST:
            return django.http.HttpResponseRedirect(
                "/legislation/add/articles?law_id=%s" % law_id
            )
        if "save-btn" in request.POST:
            return django.http.HttpResponseRedirect(
                "/legislation/articles?law_id=%s" % law_id
            )


class LegislationView(UserPatchMixin, views.View):

    template = "legislationView.html"

    def get(self, request, legislation_pk):
        law = django.shortcuts.get_object_or_404(
            models.Legislation, pk=legislation_pk)
        law.all_tags = taxonomy_to_string(law, tags=True)
        law.all_classifications = taxonomy_to_string(law, classification=True)
        return django.shortcuts.render(request, self.template, {"law": law})


class LegislationPagesView(UserPatchMixin, views.View):

    def get(self, request):
        law = models.Legislation.objects.get(pk=request.GET.get("law_id"))
        pages = law.page.all()
        content = {}
        for page in pages:
            content[page.page_number] = page.page_text

        return django.http.JsonResponse(content)


class ArticlesList(UserPatchMixin, views.View):

    template = "articlesList.html"

    def get(self, request):
        law = models.Legislation.objects.get(
            pk=request.GET.get("law_id")
        )
        articles = law.articles.all()

        for article in articles:
            article.all_tags = taxonomy_to_string(article, tags=True)
            article.all_classifications = taxonomy_to_string(
                article, classification=True
            )

        return django.shortcuts.render(request, self.template, {
            "articles": articles,
            "law": law
        })


class EditArticles(UserPatchMixin, mixins.LoginRequiredMixin, views.View):

    login_url = constants.LOGIN_URL
    template = "editArticle.html"

    def get(self, request):
        article = models.LegislationArticle.objects.get(
            pk=request.GET.get("article_id")
        )

        return django.shortcuts.render(request, self.template, {
            "article": article,
            "starting_page": article.legislation_page,
            "law": article.legislation,
            "selected_tags": [tag.name for tag in article.tags.all()],
            "selected_classifications": [
                classification.name
                for classification in article.classifications.all()
            ],
            "tag_groups": [
                LegislationAdd.TagGroupRender(tag_group)
                for tag_group in models.TaxonomyTagGroup.objects.all()
            ],
            "classifications": LegislationAdd.taxonomy_classifications
        })

    def post(self, request):
        article_id = request.POST.get("article_id")
        models.LegislationArticle.objects.filter(pk=article_id).update(
            text=request.POST.get("legislation_text"),
            code=request.POST.get("code"),
            legislation_page=request.POST.get("legislation_page")
        )

        article = models.LegislationArticle.objects.get(pk=article_id)
        article.tags.clear()
        article.classifications.clear()
        article.tags = selected_taxonomy(request, is_tags=True)
        article.classifications = selected_taxonomy(request)
        article.save()

        return django.http.HttpResponseRedirect(
            "/legislation/articles?law_id=%s" % request.POST.get("law_id")
        )


class LegislationEditView(UserPatchMixin, mixins.LoginRequiredMixin, views.View):

    login_url = constants.LOGIN_URL
    template = "legislationEditView.html"

    def get_law_patched_with_request(self, request, law):
        if request.POST["title"] != law.title:
            law.title = request.POST["title"]
        if request.POST["abstract"] != law.abstract:
            law.abstract = request.POST["abstract"]

        country = models.Country.objects.filter(
            iso=request.POST["country"])[0]
        if law.country != country:
            law.country = country
        if request.POST["language"] != law.language:
            law.language = request.POST["language"]
        if request.POST["law_type"] != law.law_type:
            law.law_type = request.POST["law_type"]
        if request.POST["geo"] != law.geo_coverage:
            law.geo_coverage = request.POST["geo"]

        if request.POST["website"] != law.website:
            law.website = request.POST["website"]
        if request.POST["source"] != law.source:
            law.source = request.POST["source"]
        if request.POST["source_type"] != law.source_type:
            law.source_type = request.POST["source_type"]

        if int(request.POST["law_year"]) != law.year:
            law.year = int(request.POST["law_year"])
        if int(request.POST["amendment_year"]) != law.year_amendment:
            law.year_amendment = request.POST["amendment_year"]
        if request.POST["year_of_adoption_mention"] != law.year_mention:
            law.year_mention = request.POST["year_of_adoption_mention"]
        return law

    def get_render_context(self, request, law, errors=None, is_post=False):
        countries = sorted(models.Country.objects.all(), key=lambda c: c.name)
        if is_post:
            selected_tags = [
                tag.name for tag in selected_taxonomy(request, is_tags=True)]
            selected_class = [_cls.name for _cls in selected_taxonomy(request)]
        else:
            selected_tags = [tag.name for tag in law.tags.all()]
            selected_class = [_cls.name for _cls in law.classifications.all()]
        return {
            "law": law,
            "countries": countries,
            "available_languages": constants.ALL_LANGUAGES,
            "legislation_type": constants.LEGISLATION_TYPE,
            "tag_groups": [
                LegislationAdd.TagGroupRender(tag_group)
                for tag_group in models.TaxonomyTagGroup.objects.all()
            ],
            "classifications": LegislationAdd.taxonomy_classifications,
            "adoption_years": LEGISLATION_YEAR_RANGE,
            "selected_tags": selected_tags,
            "selected_classifications": selected_class,
            "source_types": constants.SOURCE_TYPE,
            "geo_coverage": constants.GEOGRAPHICAL_COVERAGE,
            "errors": errors
        }

    def get(self, request):
        law_id = request.GET.get("law_id", None)
        if law_id is None or law_id == '':
            return response_error(
                request, ["Internal error: No legislation id was provided!"])
        try:
            law = models.Legislation.objects.get(pk=int(law_id))
        except models.Legislation.DoesNotExist:
            return response_error(
                request,
                ["Internal error: No legislation found for id %s!" % law_id]
            )
        return django.shortcuts.render(
            request,
            self.template,
            self.get_render_context(request, law)
        )

    def post(self, request):
        has_pdf = "pdf_file" in request.FILES
        law_id = request.POST.get("save-law-id-btn", None)

        if law_id is None:
            return response_error(
                request, ["Internal error: No legislation id was provided!"])
        try:
            law = models.Legislation.objects.get(pk=int(law_id))
        except models.Legislation.DoesNotExist:
            return response_error(
                request,
                ["Internal error: No legislation found for id %s!" % law_id]
            )

        errors = {}

        if has_pdf:
            pdf = LegislationAdd.legislation_form_get_pdf_file(
                request.FILES['pdf_file'], errors)
        LegislationAdd.legislation_form_check_year_details(
            request.POST["year_of_adoption_mention"], errors)
        law = self.get_law_patched_with_request(request, law)

        if errors:
            context = self.get_render_context(
                request, law, errors=errors, is_post=True)
            return django.shortcuts.render(request, self.template, context)

        if has_pdf:
            law.pdf_file_name = request.FILES['pdf_file'].name
            law.pdf_file.save(
                request.FILES['pdf_file'].name, request.FILES['pdf_file'].file)
            models.LegislationPage.objects.filter(legislation=law).delete()
            LegislationAdd.legislation_save_pdf_pages(law, pdf)
        law.tags.clear()
        law.classifications.clear()
        law.tags = selected_taxonomy(request, is_tags=True)
        law.classifications = selected_taxonomy(request)
        law.save()

        return django.http.HttpResponseRedirect("/legislation/")


class Register(views.View):
    """ Registration form.
    """

    template = "register.html"

    @staticmethod
    def _context(**kwargs):
        def _skip_admin(name):
            return name != roles.SiteAdministrator.get_name()

        default = (
            ('countries', models.Country.objects.order_by('name')),
            ('roles', filter(_skip_admin, RolesManager.get_roles_names()))
        )

        return dict(default + tuple(kwargs.items()))

    def _validate_post(self, request):
        def _validate(request, field, msg, must_pass=lambda val: val):
            """ accepts an "extra" validator function """
            valid = must_pass(request.POST.get(field))
            return (field, msg) if not valid else None

        validate = partial(_validate, request)
        validate_email = (
            validate('email', 'Email is required!') or
            validate(
                'email', 'Email already registered!',
                must_pass=lambda email: len(
                    User.objects.filter(
                        Q(email=email) | Q(username=email))) == 0
            )
        )
        validate_country = validate('country', 'Country is required!')
        validate_role = validate(
            'role', 'You must choose a role!',
            must_pass=RolesManager.retrieve_role
        )

        return dict(
            filter(bool, (validate_email, validate_country, validate_role)))

    def get(self, request):
        context = self._context()
        return django.shortcuts.render(request, self.template, context)

    def _respond_with_errors(self, errors, request):
        # preserve input data
        default = {
            fname: request.POST.get(fname) for
            fname in ('email', 'country', 'role')
        }

        return self._context(errors=errors, default=default)

    def _respond_with_success(self, request):
        role = RolesManager.retrieve_role(request.POST.get('role'))

        # add user, mark as inactive
        email = request.POST.get('email')
        user = User.objects.create_user(email, email=email)
        user.is_active = False
        user.save()

        # set country
        country = request.POST.get('country')
        user.userprofile.home_country = models.Country.objects.get(iso=country)
        user.userprofile.affiliation = request.POST.get('affiliation')
        user.userprofile.position = request.POST.get('position')
        user.userprofile.save()

        # grant role
        role.assign_role_to_user(user)

        # send email to admins
        admin_emails = (
            User.objects
            .filter(is_staff=True)
            .values_list('email', flat=True)
        )
        mail_template = get_template('mail/new_registration.html').render()
        mail_subject = 'New user registration'
        send_mail(
            mail_subject,
            mail_template,
            settings.EMAIL_FROM,
            admin_emails,
            html_message=mail_template,
            fail_silently=False
        )

        return self._context(success=True)

    @transaction.atomic
    def post(self, request):
        errors = self._validate_post(request)
        context = (
            self._respond_with_errors(errors, request) if errors
            else self._respond_with_success(request)
        )
        return django.shortcuts.render(request, self.template, context)
