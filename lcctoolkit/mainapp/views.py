import json
import pdftotext
import re
import time

import django.db
import django.contrib.auth as auth
import django.contrib.auth.mixins as mixins
import django.shortcuts
import django.http
import django.views

import lcctoolkit.mainapp.constants as constants
import lcctoolkit.mainapp.models as models
import lcctoolkit.settings as settings

LEGISLATION_YEAR_RANGE = range(1945, constants.LEGISLATION_DEFAULT_YEAR + 1)


def response_error(request, errors, template="message.html"):

    return django.shortcuts.render(request, template, {"errors": errors})


class UserPatchMixin():

    def dispatch(self, request, *args, **kwargs):
        self.user_profile = None
        if request.user.is_authenticated:
            self.user_profile = models.UserProfile.objects.get(user=request.user)
            request.user_profile = self.user_profile
        return super(UserPatchMixin, self).dispatch(request, *args, **kwargs)


class Index(UserPatchMixin, django.views.View):

    def get(self, request):
        return django.http.HttpResponseRedirect("/legislation/")


class Login(django.views.View):

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


class Logout(django.views.View):

    def get(self, request):
        auth.logout(request)
        return django.http.HttpResponseRedirect("/")


class LegislationExplorer(UserPatchMixin, django.views.View):

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
                laws = laws.filter(country=req_dict.get('country')[0])

            if req_dict.get('type'):
                laws = laws.filter(law_type=req_dict.get('type')[0])

        laws = laws.order_by('-pk')

        # For now, tags and classifications are displayed as a string
        # @TODO find a better approach
        for law in laws:
            law.all_tags = ", ".join(
                list(law.tags.values_list('name', flat=True)))
            law.all_classifications = ", ".join(
                list(law.classifications.values_list('name', flat=True)))

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


def legislation_form_check_year_details(year_details, errors):
    years_in_year_details = [
        int(year)
        for year in re.findall('\d\d\d\d', year_details)
    ]

    if years_in_year_details:
        if not any(year in LEGISLATION_YEAR_RANGE
                   for year in years_in_year_details):
            errors["year_details"] = "Please add a year in %d-%d range." % (
                LEGISLATION_YEAR_RANGE[0], LEGISLATION_YEAR_RANGE[-1]
            )
    else:
        errors["year_details"] = "'Additional date details' field needs a 4 digit year."


def legislation_form_get_pdf_file(file, errors):
    try:
        return pdftotext.PDF(file)
    except pdftotext.Error:
        errors["pdf"] = "The .pdf file is corrupted. Please reupload it."


def legislation_save_pdf_pages(law, pdf):
    if settings.DEBUG:
        time_to_load_pdf = time.time()
    if settings.DEBUG:
        print("INFO: FS pdf file load time: %fs" %
              (time.time() - time_to_load_pdf))
        time_begin_transaction = time.time()

    with django.db.transaction.atomic():
        for idx, page in enumerate(pdf):
            models.LegislationPage(
                page_text="<pre>%s</pre>" % page,
                page_number=idx + 1,
                legislation=law
            ).save()

    if settings.DEBUG:
        print("INFO: ORM models.LegislationPages save time: %fs" %
              (time.time() - time_begin_transaction))


class LegislationAdd(UserPatchMixin, mixins.LoginRequiredMixin, django.views.View):

    login_url = constants.LOGIN_URL
    template = "legislationAdd.html"
    taxonomy_classifications = models.TaxonomyClassification.\
        objects.filter(level=0).order_by('code')

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
            "adoption_years": LEGISLATION_YEAR_RANGE,
            "classifications": LegislationAdd.taxonomy_classifications
        })

    def post(self, request):

        def check_year_details(year_details, errors):
            years_in_year_details = [
                int(year)
                for year in re.findall('\d\d\d\d', year_details)
            ]

            if years_in_year_details:
                if not any(year in LEGISLATION_YEAR_RANGE
                           for year in years_in_year_details):
                    errors["year_details"] = "Please add a year in %d-%d range." % (
                        LEGISLATION_YEAR_RANGE[0], LEGISLATION_YEAR_RANGE[-1]
                    )
            else:
                errors["year_details"] = "'Additional date details' field needs a 4 digit year."

        def get_text_from_pdf(file, errors):
            try:
                return pdftotext.PDF(file)
            except pdftotext.Error:
                errors["pdf"] = "The .pdf file is corrupted. Please reupload it."

        title = request.POST["title"]
        abstract = request.POST["abstract"]
        country = models.Country.objects.filter(
            iso=request.POST["country"])[0]
        language = request.POST["language"]
        law_type = request.POST["law_type"]
        year = int(request.POST["law_year"])
        year_details = request.POST["year_of_adoption_mention"]
        uploaded_file = request.FILES['pdf_file']
        tags = [tag for tag in selected_taxonomy(request, is_tags=True)]
        classifications = [
            classification
            for classification in selected_taxonomy(request)
        ]

        errors = {}
        check_year_details(year_details, errors)
        pdf = legislation_form_get_pdf_file(uploaded_file, errors)

        if errors:
            return django.shortcuts.render(request, self.template, {
                "title": title,
                "abstract": abstract,
                "selected_country": country,
                "selected_language": language,
                "selected_law_type": law_type,
                "selected_year_of_adoption": year,
                "selected_year_details": year_details,
                "selected_tags": [tag.name for tag in tags],
                "selected_classifications": [cl.name for cl in classifications],
                "countries": sorted(models.Country.objects.all(), key=lambda c: c.name),
                "legislation_type": constants.LEGISLATION_TYPE,
                "tag_groups": [
                    LegislationAdd.TagGroupRender(tag_group)
                    for tag_group in models.TaxonomyTagGroup.objects.all()
                ],
                "available_languages": constants.ALL_LANGUAGES,
                "adoption_years": LEGISLATION_YEAR_RANGE,
                "classifications": LegislationAdd.taxonomy_classifications,
                "errors": errors
            })

        law_obj = models.Legislation(
            title=title,
            abstract=abstract,
            country=country,
            language=language,
            law_type=law_type,
            year=year,
            year_mention=year_details,
            pdf_file_name=uploaded_file.name
        )

        law_obj.pdf_file.save(uploaded_file.name, uploaded_file.file)
        law_obj.save()

        for tag in tags:
            law_obj.tags.add(tag)
        for classification in classifications:
            law_obj.classifications.add(classification)

        legislation_save_pdf_pages(law_obj, pdf)

        if "save-and-continue-btn" in request.POST:
            return django.http.HttpResponseRedirect(
                "/legislation/add/articles?law_id=%s" % str(law_obj.pk)
            )
        if "save-btn" in request.POST:
            return django.http.HttpResponseRedirect("/legislation/")


class LegislationManagerArticles(UserPatchMixin, mixins.LoginRequiredMixin, django.views.View):

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
        else:
            return django.http.HttpResponseRedirect("/legislation/")


class LegislationView(UserPatchMixin, django.views.View):

    template = "legislationView.html"

    def get(self, request, legislation_pk):
        law = django.shortcuts.get_object_or_404(
            models.Legislation, pk=legislation_pk)
        law.all_tags = ", ".join(
            list(law.tags.values_list('name', flat=True)))
        law.all_classifications = ", ".join(
            list(law.classifications.values_list('name', flat=True)))
        return django.shortcuts.render(request, self.template, {"law": law})


class LegislationPagesView(django.views.View):

    def get(self, request):
        law = models.Legislation.objects.get(pk=request.GET.get("law_id"))
        pages = law.page.all()
        content = {}
        for page in pages:
            content[page.page_number] = page.page_text

        return django.http.JsonResponse(content)


class LegislationEditView(UserPatchMixin, mixins.LoginRequiredMixin, django.views.View):

    login_url = constants.LOGIN_URL
    template = "legislationEditView.html"

    def get_law_patched_with_request(self, request, law):
        if request.POST["title"] != law.title:
            law.title = request.POST["title"]
        if request.POST["abstract"] != law.abstract:
            law.abstract = request.POST["abstract"]
        if request.POST["law_type"] != law.law_type:
            law.law_type = request.POST["law_type"]
        country = models.Country.objects.filter(
            iso=request.POST["country"])[0]
        if law.country != country:
            law.country = country
        if request.POST["language"] != law.language:
            law.language = request.POST["language"]
        if int(request.POST["law_year"]) != law.year:
            law.year = int(request.POST["law_year"])
        if request.POST["year_of_adoption_mention"] != law.year_mention:
            law.year_mention = request.POST["year_of_adoption_mention"]
        return law

    def get_render_context(self, request, law, errors=None, is_post=False):
        countries = sorted(models.Country.objects.all(), key=lambda c: c.name)
        if is_post:
            selected_tags = [tag.name for tag in selected_taxonomy(request, is_tags=True)]
            selected_class = [ _cls.name for _cls in selected_taxonomy(request)]
        else:
            selected_tags = [tag.name for tag in law.tags.all()]
            selected_class = [_cls.name for _cls in law.classifications.all()]
        return {
            "law": law,
            "countries": countries,
            "available_languages": constants.ALL_LANGUAGES,
            "legislation_type": constants.LEGISLATION_TYPE,
            "tag_groups": [LegislationAdd.TagGroupRender(tag_group) 
                            for tag_group in models.TaxonomyTagGroup.objects.all()],
            "classifications": LegislationAdd.taxonomy_classifications,
            "adoption_years": LEGISLATION_YEAR_RANGE,
            "selected_tags": selected_tags,
            "selected_classifications": selected_class, 
            "errors": errors
        }

    def get(self, request):
        law_id = request.GET.get("law_id", None)
        if law_id is None  or law_id == '':
            return response_error(
                request, ["Internal error: No legislation id was provided!"])
        try:
            law = models.Legislation.objects.get(pk=int(law_id))
            countries = sorted(models.Country.objects.all(), key=lambda c: c.name)
        except models.Legislation.DoesNotExist as e:
                    return response_error(
                request, ["Internal error: No legislation found for id %s!" % law_id])
        return django.shortcuts.render(request, self.template, self.get_render_context(request, law))

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
                request, ["Internal error: No legislation found for id %s!" % law_id])
        errors = {}
        if has_pdf:
            pdf = legislation_form_get_pdf_file(request.FILES['pdf_file'], errors)
        legislation_form_check_year_details(request.POST["year_of_adoption_mention"], errors)
        law = self.get_law_patched_with_request(request, law)
        if errors:
            return django.shortcuts.render(request, self.template, 
                    self.get_render_context(request, law, errors=errors, is_post=True))
        if has_pdf:
            law.pdf_file_name = request.FILES['pdf_file'].name
            law.pdf_file.save(
                request.FILES['pdf_file'].name, request.FILES['pdf_file'].file)
            models.LegislationPage.objects.filter(legislation=law).delete()
            legislation_save_pdf_pages(law, pdf)
        law.tags.clear()
        law.classifications.clear()
        law.save()
        for tag in selected_taxonomy(request, is_tags=True):
            law.tags.add(tag)
        for classification in selected_taxonomy(request):
            law.classifications.add(classification)
        return django.http.HttpResponseRedirect("/legislation/")
