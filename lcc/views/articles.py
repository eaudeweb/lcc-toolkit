from django.contrib.auth import mixins
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView, CreateView, UpdateView

from lcc import constants, models, forms
from lcc.views.base import (
    UserPatchMixin, TagGroupRender, TaxonomyFormMixin,
    taxonomy_to_string,
)


class ArticleFormMixin:
    def dispatch(self, request, *args, **kwargs):
        self.law = get_object_or_404(models.Legislation,
                                     pk=kwargs['legislation_pk'])
        return super().dispatch(request, *args, **kwargs)


class AddArticles(UserPatchMixin, mixins.LoginRequiredMixin, TaxonomyFormMixin,
                  ArticleFormMixin,
                  CreateView):
    login_url = constants.LOGIN_URL
    template_name = "legislation/articles/add.html"
    model = models.LegislationArticle
    form_class = forms.ArticleForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        last_article = self.law.articles.order_by('pk').last() \
            if self.law.articles else None
        starting_page = last_article.legislation_page if last_article else 1

        context.update(
            {
                'law': self.law,
                "starting_page": starting_page,
                "last_article": last_article,
                "add_article": True,
                "tag_groups": [
                    TagGroupRender(tag_group)
                    for tag_group in models.TaxonomyTagGroup.objects.all()
                ],
                "classifications":
                    models.TaxonomyClassification.objects.filter(
                        level=0).order_by('code')
            }
        )
        return context

    def form_valid(self, form):
        article = form.save()
        if "save-and-continue-btn" in self.request.POST:
            return HttpResponseRedirect(
                reverse('lcc:legislation:articles:add',
                        kwargs={'legislation_pk': article.legislation.pk})
            )
        if "save-btn" in self.request.POST:
            return HttpResponseRedirect(
                reverse('lcc:legislation:articles:view',
                        kwargs={'legislation_pk': article.legislation.pk})
            )


class ArticlesList(UserPatchMixin, DetailView):
    template_name = "legislation/articles/list.html"
    context_object_name = 'law'
    model = models.Legislation
    pk_url_kwarg = 'legislation_pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        articles = self.get_object().articles.all()

        for article in articles:
            article.all_tags = taxonomy_to_string(article, tags=True)
            article.all_classifications = taxonomy_to_string(
                article, classification=True
            )
        context.update({
            "articles": articles,
        })
        return context


class EditArticles(UserPatchMixin,
                   mixins.LoginRequiredMixin,
                   TaxonomyFormMixin,
                   ArticleFormMixin,
                   UpdateView):
    login_url = constants.LOGIN_URL
    template_name = "legislation/articles/edit.html"
    model = models.LegislationArticle
    context_object_name = 'article'
    form_class = forms.ArticleForm
    pk_url_kwarg = 'article_pk'

    def get_object(self, **kwargs):
        return get_object_or_404(models.LegislationArticle,
                                 pk=self.kwargs['article_pk'],
                                 legislation__pk=self.kwargs['legislation_pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.get_object()
        context.update({
            "starting_page": article.legislation_page,
            "law": article.legislation,
            "selected_tags": [tag.name for tag in article.tags.all()],
            "selected_classifications": [
                classification.name
                for classification in article.classifications.all()
            ],
            "tag_groups": [
                TagGroupRender(tag_group)
                for tag_group in models.TaxonomyTagGroup.objects.all()
            ],
            "classifications": models.TaxonomyClassification.objects.filter(
                level=0).order_by('code')
        })
        return context

    def form_invalid(self, form):
        print(form.errors)

    def form_valid(self, form):
        article = form.save()
        return HttpResponseRedirect(
            reverse('lcc:legislation:articles:view', kwargs={
                'legislation_pk': article.legislation.pk
            })
        )
