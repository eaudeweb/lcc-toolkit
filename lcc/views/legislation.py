from django import views
from django.conf import settings
from django.contrib.auth import mixins
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.generic import (
    ListView, CreateView, DetailView, UpdateView, DeleteView
)
from elasticsearch_dsl import Q

from lcc import models, constants, forms
from lcc.constants import LEGISLATION_YEAR_RANGE
from lcc.documents import LegislationDocument
from lcc.views.base import TagGroupRender, TaxonomyFormMixin


class HighlightedLaws:
    """
    This class wraps a Search instance and is compatible with Django's
    pagination API.
    """

    def __init__(self, search):
        self.search = search

    def __getitem__(self, key):
        hits = self.search[key]
        laws = []
        for hit, law in zip(hits, hits.to_queryset()):
            if hasattr(hit.meta, 'highlight'):
                highlights = hit.meta.highlight.to_dict()
                if 'abstract' in highlights:
                    law._highlighted_abstract = mark_safe(
                        ' […] '.join(highlights['abstract'])
                    )
                if 'pdf_text' in highlights:
                    law._highlighted_pdf_text = mark_safe(
                        ' […] '.join(highlights['pdf_text'])
                    )
                if 'title' in highlights:
                    law._highlighted_title = mark_safe(highlights['title'][0])
                if 'classifications_text' in highlights:
                    law._highlighted_classifications = [
                        mark_safe(classification)
                        for classification in (
                            highlights['classifications_text'][0].split('; '))
                    ]
                if 'tags_text' in highlights:
                    law._highlighted_tags = [
                        mark_safe(tag)
                        for tag in highlights['tags_text'][0].split('; ')
                    ]
            if hasattr(hit.meta, 'inner_hits'):
                law._highlighted_articles = [
                    {
                        'pk': article.pk,
                        'code': article.code,
                        'text': mark_safe(
                            ' […] '.join(
                                article.meta.highlight['articles.text'])
                        )
                    }
                    for article in hit.meta.inner_hits.articles.hits
                ]
            laws.append(law)
        return laws

    def count(self):
        return self.search.count()


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
        Note that this DOES NOT return a QuerySet object, it returms a Page
        object instead. This is necessary because by transforming an
        elasticsearch-dsl Search object into a QuerySet a lot of functionality
        is lost, so we need to make things a bit more custom.
        """

        search = LegislationDocument.search()

        # jQuery's ajax function ads `[]` to duplicated querystring parameters
        # or parameters whose values are objects, so we have to take that into
        # account when looking for our values in the querystring. More into at:
        #   - http://api.jquery.com/jQuery.param/

        # List of strings representing TaxonomyClassification ids
        classification_ids = [
            int(pk) for pk in self.request.GET.getlist('classifications[]')]

        if classification_ids:

            classifications = models.TaxonomyClassification.objects.filter(
                pk__in=classification_ids)

            top_classification_ids = []
            other_classification_ids = []

            for cl in classifications:
                if cl.level == 0:
                    top_classification_ids.append(cl.pk)
                else:
                    other_classification_ids.append(cl.pk)

            # Search root document
            root_query = Q('terms', classifications=top_classification_ids)

            # Search inside articles
            nested_query = Q(
                'nested', path='articles',
                query=Q(
                    'terms',
                    articles__classification_ids=other_classification_ids
                )
            )

            # Join queries
            search = search.query(root_query | nested_query)

        # List of strings representing TaxonomyTag ids
        tag_ids = [int(pk) for pk in self.request.GET.getlist('tags[]')]
        if tag_ids:
            # Search in root document
            root_query = Q('terms', tags=tag_ids)
            # Search inside articles
            nested_query = Q(
                'nested', path='articles',
                query=Q(
                    'terms',
                    articles__tag_ids=tag_ids
                )
            )
            # Join queries
            search = search.query(root_query | nested_query)

        # String representing country iso code
        countries = self.request.GET.getlist('countries[]')
        if countries:
            search = search.query('terms', country=countries)

        # String representing law_type
        law_types = self.request.GET.getlist('law_types[]')
        if law_types:
            search = search.query('terms', law_type=law_types)

        # String representing the minimum year allowed in the results
        from_year = self.request.GET.get('from_year')
        # String representing the maximum year allowed in the results
        to_year = self.request.GET.get('to_year')

        if all([from_year, to_year]):
            search = search.filter(
                'range', year={'gte': int(from_year), 'lte': int(to_year)})

        # String to be searched in all text fields (full-text search using
        # elasticsearch's default best_fields strategy)
        q = self.request.GET.get('q')
        if q:
            # Compose root document search
            root_query = Q(
                'multi_match', query=q, fields=[
                    'title', 'abstract', 'pdf_text', 'classifications_text',
                    'tags_text'
                ]
            )
            # Compose nested document search inside articles
            nested_query = Q(
                'nested', path='articles',
                query=Q(
                    'multi_match',
                    query=q,
                    fields=['articles.text']
                ),
                inner_hits={
                    'highlight': {
                        'fields': {'articles.text': {}}
                    }
                }
            )
            # Join the searches with OR (either result should suffice)
            search = search.query(
                root_query | nested_query
            ).highlight(
                'abstract', 'pdf_text'
            ).highlight(
                'title', 'classifications_text', 'tags_text',
                number_of_fragments=0
            )

        if not any([classification_ids, tag_ids, q]):
            # If there is no score to sort by, sort by id
            search = search.sort('id')

        all_laws = HighlightedLaws(search)

        paginator = Paginator(all_laws, settings.LAWS_PER_PAGE)

        page = self.request.GET.get('page', 1)

        try:
            laws = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            laws = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            laws = paginator.page(paginator.num_pages)
        return laws

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_tags = models.TaxonomyTagGroup.objects.all()
        top_classifications = models.TaxonomyClassification.objects.filter(
            level=0).order_by('code')
        regions = models.Region.objects.all()

        laws = self.object_list

        legislation_year = (
            LEGISLATION_YEAR_RANGE[0],
            LEGISLATION_YEAR_RANGE[len(LEGISLATION_YEAR_RANGE) - 1]
        )
        context.update({
            'laws': laws,
            'group_tags': group_tags,
            'top_classifications': top_classifications,
            'regions': regions,
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
        legislation.save_pdf_pages()

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
        pages = law.pages.all()
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
            models.LegislationPage.objects.filter(
                legislation=legislation).delete()
            legislation.save_pdf_pages()

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
