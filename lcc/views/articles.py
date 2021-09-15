from django.urls import reverse
from django.contrib.auth import mixins
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, CreateView, UpdateView, DeleteView

from lcc import models, forms
from lcc.views.base import TagGroupRender, TaxonomyFormMixin


class ArticleFormMixin:
    def dispatch(self, request, *args, **kwargs):
        self.law = get_object_or_404(models.Legislation,
                                     pk=kwargs['legislation_pk'])
        return super().dispatch(request, *args, **kwargs)


class AddArticles(mixins.LoginRequiredMixin, TaxonomyFormMixin,
                  ArticleFormMixin,
                  CreateView):
    template_name = "legislation/articles/add.html"
    model = models.LegislationArticleTree
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


class ArticlesList(DetailView):
    template_name = "legislation/articles/list.html"
    context_object_name = 'law'
    model = models.Legislation
    pk_url_kwarg = 'legislation_pk'


class EditArticles(mixins.LoginRequiredMixin,
                   TaxonomyFormMixin,
                   ArticleFormMixin,
                   UpdateView):
    template_name = "legislation/articles/edit.html"
    model = models.LegislationArticleTree
    context_object_name = 'article'
    form_class = forms.ArticleForm
    pk_url_kwarg = 'article_pk'

    def get_object(self, **kwargs):
        return get_object_or_404(models.LegislationArticleTree,
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
        article = self.get_object()
        return HttpResponseRedirect(
            reverse('lcc:legislation:articles:edit', kwargs={
                'legislation_pk': article.legislation.pk,
                'article_pk': article.pk
            })
        )

    def form_valid(self, form):
        article = form.save()
        return HttpResponseRedirect(
            reverse('lcc:legislation:articles:view', kwargs={
                'legislation_pk': article.legislation.pk
            })
        )


class DeleteArticle(mixins.LoginRequiredMixin, DeleteView):
    model = models.LegislationArticleTree
    pk_url_kwarg = 'article_pk'

    def get_success_url(self, **kwargs):
        legislation_pk = self.kwargs['legislation_pk']
        return reverse('lcc:legislation:articles:view', kwargs={
            'legislation_pk': legislation_pk
        })

    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)
