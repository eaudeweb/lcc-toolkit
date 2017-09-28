import json
import os
import pdftotext
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

        def add_legislation_page(law):
            if settings.DEBUG:
                time_to_load_pdf = time.time()
            pdf_path = os.path.join(settings.MEDIA_ROOT, law.pdf_file.name)
            with open(pdf_path, "rb") as fd:
                pdf = pdftotext.PDF(fd)
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

        law_obj = models.Legislation()
        law_obj.law_type = request.POST["law_type"]
        law_obj.title = request.POST["title"]
        law_obj.abstract = request.POST["abstract"]
        law_obj.country = models.Country.objects.filter(
            iso=request.POST["country"])[0]
        law_obj.language = request.POST["language"]
        law_obj.year = int(request.POST["law_year"])
        law_obj.pdf_file_name = request.FILES['pdf_file'].name
        law_obj.pdf_file.save(
            request.FILES['pdf_file'].name, request.FILES['pdf_file'].file)
        law_obj.save()
        for tag in selected_taxonomy(request, is_tags=True):
            law_obj.tags.add(tag)
        for classification in selected_taxonomy(request):
            law_obj.classifications.add(classification)
        # @TODO find a better way to call "add_legislation_page"
        if "save-and-continue-btn" in request.POST:
            add_legislation_page(law_obj)
            return django.http.HttpResponseRedirect(
                "/legislation/add/articles?law_id=%s" % str(law_obj.pk)
            )
        if "save-btn" in request.POST:
            add_legislation_page(law_obj)
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
