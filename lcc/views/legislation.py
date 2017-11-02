import pdftotext
import time

from django import views
from django.conf import settings
from django.contrib.auth import mixins
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import (
    ListView, CreateView, DetailView, UpdateView, DeleteView
)

from lcc import models, constants, forms
from lcc.constants import LEGISLATION_YEAR_RANGE
from lcc.documents import LegislationDocument
from lcc.views.base import TagGroupRender, TaxonomyFormMixin


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


class LegislationExplorer(ListView):
    template_name = "legislation/explorer.html"
    model = models.Legislation

    def dispatch(self, request, *args, **kwargs):
        """
        If the `partial` parameter is set, return only the list of laws,
        don't render the whole page again.
        """

        if self.request.GET.get('partial'):
            self.template_name = "legislation/_laws.html"
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """
        Perform filtering using ElasticSearch instead of Postgres.
        """

        search = LegislationDocument.search()

        # jQuery's ajax function ads `[]` to duplicated querystring parameters
        # or parameters whose values are objects, so we have to take that into
        # account when looking for our values in the querystring. More into at:
        #   - http://api.jquery.com/jQuery.param/

        # List of strings representing TaxonomyClassification ids
        classifications = self.request.GET.getlist('classifications[]')
        if classifications:
            search = search.query(
                'terms', classifications=[int(pk) for pk in classifications])

        # List of strings representing TaxonomyTag ids
        tags = self.request.GET.getlist('tags[]')
        if tags:
            search = search.query(
                'terms', tags=[int(pk) for pk in tags])

        # String representing country iso code
        country = self.request.GET.get('country')
        if country:
            search = search.query('term', country=country)

        # String representing law_type
        law_type = self.request.GET.get('law_type')
        if law_type:
            search = search.query('term', law_type=law_type)

        # String to be searched in all text fields (full-text search using
        # elasticsearch's default best_fields strategy)
        q = self.request.GET.get('q')
        if q:
            search = search.query(
                'multi_match', query=q, fields=['title', 'abstract'])
        # TODO: Implement proper pagination!
        return search[0:10000].to_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_tags = models.TaxonomyTagGroup.objects.all()
        top_classifications = models.TaxonomyClassification.objects.filter(
            level=0).order_by('code')
        countries = models.Country.objects.all()

        laws = self.object_list

        legislation_year = (
            LEGISLATION_YEAR_RANGE[0],
            LEGISLATION_YEAR_RANGE[len(LEGISLATION_YEAR_RANGE) - 1]
        )
        context.update({
            'laws': laws,
            'group_tags': group_tags,
            'top_classifications': top_classifications,
            'countries': countries,
            'legislation_type': constants.LEGISLATION_TYPE,
            'legislation_year': legislation_year
        })
        return context


class LegislationAdd(mixins.LoginRequiredMixin, TaxonomyFormMixin,
                     CreateView):
    template_name = "legislation/add.html"
    form_class = forms.LegislationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        countries = sorted(models.Country.objects.all(), key=lambda c: c.name)
        context.update({
            "countries": countries,
            "legislation_type": constants.LEGISLATION_TYPE,
            "tag_groups": [
                TagGroupRender(tag_group)
                for tag_group in models.TaxonomyTagGroup.objects.all()
            ],
            "available_languages": constants.ALL_LANGUAGES,
            "source_types": constants.SOURCE_TYPE,
            "geo_coverage": constants.GEOGRAPHICAL_COVERAGE,
            "adoption_years": LEGISLATION_YEAR_RANGE,
            "classifications": models.TaxonomyClassification.objects.filter(
                level=0).order_by('code')
        })
        return context

    def form_valid(self, form):
        legislation = form.save()
        pdf = pdftotext.PDF(legislation.pdf_file)
        legislation_save_pdf_pages(legislation, pdf)

        if "save-and-continue-btn" in self.request.POST:
            return HttpResponseRedirect(
                reverse('lcc:legislation:articles:add',
                        kwargs={'legislation_pk': legislation.pk})
            )
        if "save-btn" in self.request.POST:
            return HttpResponseRedirect(reverse("lcc:legislation:explorer"))


class LegislationView(DetailView):
    template_name = "legislation/detail.html"
    pk_url_kwarg = 'legislation_pk'
    model = models.Legislation
    context_object_name = 'law'


class LegislationPagesView(views.View):

    def get(self, request, *args, **kwargs):
        law = get_object_or_404(models.Legislation,
                                pk=kwargs['legislation_pk'])
        pages = law.page.all()
        content = {}
        for page in pages:
            content[page.page_number] = page.page_text

        return JsonResponse(content)


class LegislationEditView(mixins.LoginRequiredMixin, TaxonomyFormMixin,
                          UpdateView):
    template_name = "legislation/edit.html"
    model = models.Legislation
    form_class = forms.LegislationForm
    pk_url_kwarg = 'legislation_pk'
    context_object_name = 'law'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        countries = sorted(models.Country.objects.all(), key=lambda c: c.name)
        context.update({
            "countries": countries,
            "available_languages": constants.ALL_LANGUAGES,
            "legislation_type": constants.LEGISLATION_TYPE,
            "tag_groups": [
                TagGroupRender(tag_group)
                for tag_group in models.TaxonomyTagGroup.objects.all()
            ],
            "classifications": models.TaxonomyClassification.objects.filter(
                level=0).order_by('code'),
            "adoption_years": LEGISLATION_YEAR_RANGE,
            "source_types": constants.SOURCE_TYPE,
            "geo_coverage": constants.GEOGRAPHICAL_COVERAGE,
        })
        return context

    def form_valid(self, form):
        legislation = form.save()
        if 'pdf_file' in self.request.FILES:
            pdf = pdftotext.PDF(legislation.pdf_file)
            models.LegislationPage.objects.filter(
                legislation=legislation).delete()
            legislation_save_pdf_pages(legislation, pdf)

        return HttpResponseRedirect(
            reverse('lcc:legislation:details',
                    kwargs={'legislation_pk': legislation.pk})
        )


class LegislationDeleteView(mixins.LoginRequiredMixin, DeleteView):
    model = models.Legislation
    pk_url_kwarg = 'legislation_pk'

    def get_success_url(self, **kwargs):
        return reverse("lcc:legislation:explorer")

    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)
