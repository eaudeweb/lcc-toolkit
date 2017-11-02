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
from lcc.views.base import (
    TagGroupRender,
    taxonomy_to_string,
    TaxonomyFormMixin)


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_tags = models.TaxonomyTagGroup.objects.all()
        top_classifications = models.TaxonomyClassification.objects \
            .filter(level=0).order_by('code')
        countries = models.Country.objects.all()

        req_dict = dict(self.request.GET)
        laws = self.get_queryset()
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

    def get_object(self, queryset=None):
        law = super().get_object(queryset)
        law.all_tags = taxonomy_to_string(law, tags=True)
        law.all_classifications = taxonomy_to_string(law, classification=True)
        return law


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
