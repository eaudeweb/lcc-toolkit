import json

import django.contrib.auth as auth
import django.shortcuts
import django.http
import django.views

import lcctoolkit.mainapp.constants as constants
import lcctoolkit.mainapp.models as models


class Index(django.views.View):

    template = "index.html"

    def get(self, request):
        return django.shortcuts.render(request, self.template)


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


class LegislationExplorer(django.views.View):

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

            if req_dict.get('classification'):
                laws = laws.filter(
                    classifications=req_dict.get('classification')[0])

            if req_dict.get('country'):
                laws = laws.filter(country=req_dict.get('country')[0])

            if req_dict.get('type'):
                laws = laws.filter(law_type=req_dict.get('type')[0])

        laws = laws.distinct()

        # For now, tags are displayed as a string
        # @TODO find a better approach
        for law in laws:
            law.all_tags = ", ".join(
                list(law.tags.values_list('name', flat=True)))

        legislation_year = (
            constants.LEGISLATION_YEAR_RANGE[0][0],
            constants.LEGISLATION_YEAR_RANGE[-1][0]
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


class LegislationAdd(django.views.View):

    template = "legislationAdd.html"

    class TagGroupRender():

        def __init__(self, tag_group):
            self.name = tag_group.name
            self.pk = tag_group.pk
            self.tags = [{'name': tag.name, 'pk': tag.pk}
                         for tag in models.TaxonomyTag.objects.filter(
                group=tag_group)]

    def get(self, request):
        taxonomy_classifications = models.TaxonomyClassification.\
            objects.filter(level=0).order_by('code')
        return django.shortcuts.render(request, self.template, {
            "countries": models.Country.objects.all(),
            "legislation_type": constants.LEGISLATION_TYPE,
            "tag_groups": [LegislationAdd.TagGroupRender(tag_group)
                           for tag_group in models.TaxonomyTagGroup.objects.all()],
            "classifications": taxonomy_classifications,
            "available_languages": constants.ALL_LANGUAGES,
            "adoption_years": constants.LEGISLATION_YEAR_RANGE
        })

    def post(self, request):

        def selected_taxonomy(request, is_tags=False):
            selector = "classification"
            if is_tags:
                selector = "tag"
            selected_ids = [int(el.split('_')[1])
                            for el in request.POST.keys() if el.startswith(selector + "_")]
            if is_tags:
                return models.TaxonomyTag.objects.filter(pk__in=selected_ids)
            else:
                return models.TaxonomyClassification.objects.filter(pk__in=selected_ids)

        def selected_tags(request):
            selected_tag_ids = [int(el.split('_')[1])
                                for el in request.POST.keys() if el.startswith("tag_")]
            return models.TaxonomyTag.objects.filter(pk__in=selected_tag_ids)

        new_law = models.Legislation()
        new_law.law_type = request.POST["law_type"]
        new_law.title = request.POST["title"]
        new_law.abstract = request.POST["abstract"]
        new_law.country = models.Country.objects.filter(
            iso=request.POST["country"])[0]
        new_law.language = request.POST["language"]
        new_law.year = int(request.POST["law_year"])
        new_law.pdf_file.save(
            request.FILES['pdf_file'].name, request.FILES['pdf_file'].file)
        for tag in selected_taxonomy(request, is_tags=True):
            new_law.tags.add(tag)
        for classification in selected_taxonomy(request):
            new_law.classifications.add(classification)
        new_law.save()
        return django.http.HttpResponseRedirect("/legislation/")
