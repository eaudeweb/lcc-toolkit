import json
import pdftotext
import re
import time

from django import views
from django.conf import settings
from django.contrib import auth
from django.contrib.auth import mixins
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse

import lcc.constants as constants
import lcc.models as models

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
        return HttpResponseRedirect(reverse('lcc:legislation:explorer'))


class Login(views.View):
    template = "login.html"

    def get(self, request):
        return render(request, self.template)

    def post(self, request):
        user = auth.authenticate(
            request,
            username=request.POST[constants.POST_DATA_USERNAME_KEY],
            password=request.POST[constants.POST_DATA_PASSWORD_KEY]
        )
        if user:
            auth.login(request, user)
            return HttpResponse(
                json.dumps({'msg': constants.AJAX_RETURN_SUCCESS}))
        else:
            return HttpResponse(
                json.dumps({'msg': constants.AJAX_RETURN_FAILURE}))


class Logout(views.View):
    def get(self, request):
        auth.logout(request)
        return HttpResponseRedirect(reverse('lcc:index'))


class LegislationExplorer(UserPatchMixin, views.View):
    template = "legislation/explorer.html"

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

        return render(request, self.template, context)


class LegislationAdd(UserPatchMixin, mixins.LoginRequiredMixin, views.View):
    login_url = constants.LOGIN_URL
    template = "legislation/add.html"
    taxonomy_classifications = models.TaxonomyClassification. \
        objects.filter(level=0).order_by('code')

    @staticmethod
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

    @staticmethod
    def legislation_form_get_pdf_file(file, errors):
        try:
            return pdftotext.PDF(file)
        except pdftotext.Error:
            errors["pdf"] = "The .pdf file is corrupted. Please reupload it."

    @staticmethod
    def legislation_form_check_website(website, errors):
        url = URLValidator()
        try:
            url(website)
        except ValidationError:
            errors["website"] = "Please enter a valid website."

    @staticmethod
    def legislation_save_pdf_pages(law, pdf):
        if settings.DEBUG:
            time_to_load_pdf = time.time()
        if settings.DEBUG:
            print("INFO: FS pdf file load time: %fs" %
                  (time.time() - time_to_load_pdf))
            time_begin_transaction = time.time()

        with transaction.atomic():
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
        return render(request, self.template, {
            "countries": countries,
            "user_country": request.user_profile.country,
            "legislation_type": constants.LEGISLATION_TYPE,
            "tag_groups": [
                LegislationAdd.TagGroupRender(tag_group)
                for tag_group in models.TaxonomyTagGroup.objects.all()
            ],
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

        errors = {}
        self.legislation_form_check_year_details(year_details, errors)
        self.legislation_form_check_website(website, errors)
        pdf = self.legislation_form_get_pdf_file(uploaded_file, errors)

        if errors:
            return render(request, self.template, {
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
            return HttpResponseRedirect(
                reverse('lcc:legislation:articles:add',
                        kwargs={'legislation_pk': law_obj.pk})
            )
        if "save-btn" in request.POST:
            return HttpResponseRedirect(reverse("lcc:legislation:explorer"))


class AddArticles(UserPatchMixin, mixins.LoginRequiredMixin, views.View):
    login_url = constants.LOGIN_URL
    template = "legislation/articles/add.html"

    def get(self, request, *args, **kwargs):
        # WIP
        law = get_object_or_404(models.Legislation,
                                pk=kwargs['legislation_pk'])
        if law.articles:
            last_article = law.articles.order_by('pk').last()
        else:
            last_article = None

        if last_article:
            starting_page = last_article.legislation_page
        else:
            starting_page = 1

        return render(request, self.template, {
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

    def post(self, request, *args, **kwargs):
        article_obj = models.LegislationArticle()
        law = get_object_or_404(models.Legislation,
                                pk=kwargs['legislation_pk'])
        article_obj.code = request.POST.get("code")
        article_obj.text = request.POST.get("legislation_text")
        article_obj.legislation = models.Legislation.objects.get(
            pk=law.pk)
        article_obj.legislation_page = request.POST.get("page")
        article_obj.save()

        for tag in selected_taxonomy(request, is_tags=True):
            article_obj.tags.add(tag)
        for classification in selected_taxonomy(request):
            article_obj.classifications.add(classification)

        if "save-and-continue-btn" in request.POST:
            return HttpResponseRedirect(
                reverse('lcc:legislation:articles:add',
                        kwargs={'legislation_pk': law.pk})
            )
        if "save-btn" in request.POST:
            return HttpResponseRedirect(
                reverse('lcc:legislation:articles:view',
                        kwargs={'legislation_pk': law.pk})
            )


class LegislationView(UserPatchMixin, views.View):
    template = "legislation/detail.html"

    def get(self, request, legislation_pk):
        law = get_object_or_404(
            models.Legislation, pk=legislation_pk)
        law.all_tags = taxonomy_to_string(law, tags=True)
        law.all_classifications = taxonomy_to_string(law, classification=True)
        return render(request, self.template, {"law": law})


class LegislationPagesView(UserPatchMixin, views.View):
    def get(self, request, *args, **kwargs):
        law = get_object_or_404(models.Legislation,
                                pk=kwargs['legislation_pk'])
        pages = law.page.all()
        content = {}
        for page in pages:
            content[page.page_number] = page.page_text

        return JsonResponse(content)


class ArticlesList(UserPatchMixin, views.View):
    template = "legislation/articles/list.html"

    def get(self, request, *args, **kwargs):
        law = get_object_or_404(models.Legislation,
                                pk=kwargs['legislation_pk'])
        articles = law.articles.all()

        for article in articles:
            article.all_tags = taxonomy_to_string(article, tags=True)
            article.all_classifications = taxonomy_to_string(
                article, classification=True
            )

        return render(request, self.template, {
            "articles": articles,
            "law": law
        })


class EditArticles(UserPatchMixin, mixins.LoginRequiredMixin, views.View):
    login_url = constants.LOGIN_URL
    template = "legislation/articles/edit.html"

    def get(self, request, *args, **kwargs):
        article = get_object_or_404(models.LegislationArticle,
                                    pk=kwargs['article_pk'],
                                    legislation__pk=kwargs['legislation_pk'])

        return render(request, self.template, {
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

    def post(self, request, *args, **kwargs):
        article = get_object_or_404(models.LegislationArticle,
                                    pk=kwargs['article_pk'],
                                    legislation__pk=kwargs['legislation_pk'])
        models.LegislationArticle.objects.filter(pk=article.pk).update(
            text=request.POST.get("legislation_text"),
            code=request.POST.get("code"),
            legislation_page=request.POST.get("legislation_page")
        )

        article.tags.clear()
        article.classifications.clear()
        article.tags = selected_taxonomy(request, is_tags=True)
        article.classifications = selected_taxonomy(request)
        article.save()

        return HttpResponseRedirect(
            reverse('lcc:legislation:articles:view',
                    kwargs={'legislation_pk': article.legislation.pk,
                            'article_pk': article.pk})
            )


class LegislationEditView(UserPatchMixin, mixins.LoginRequiredMixin, views.View):
    login_url = constants.LOGIN_URL
    template = "legislation/edit.html"

    @staticmethod
    def get_law_patched_with_request(request, law):
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

    @staticmethod
    def get_render_context(request, law, errors=None, is_post=False):
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

    def get(self, request, *args, **kwargs):
        law = get_object_or_404(models.Legislation,
                                pk=kwargs['legislation_pk'])
        return render(
            request,
            self.template,
            self.get_render_context(request, law)
        )

    def post(self, request, *args, **kwargs):
        has_pdf = "pdf_file" in request.FILES
        law = get_object_or_404(models.Legislation,
                                pk=kwargs['legislation_pk'])
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
            return render(request, self.template, context)

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

        return HttpResponseRedirect(reverse('lcc:legislation:explorer'))
