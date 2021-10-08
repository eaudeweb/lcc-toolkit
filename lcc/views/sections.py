from django.urls import reverse
from django.contrib.auth import mixins
from django.contrib.postgres.fields import ArrayField
from django.db.models import OuterRef, Subquery, IntegerField
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, CreateView, UpdateView, DeleteView

from lcc import models, forms
from lcc.views.base import TagGroupRender, TaxonomyFormMixin

from mptt.templatetags.mptt_tags import cache_tree_children


class SectionFormMixin:
    def dispatch(self, request, *args, **kwargs):
        self.law = get_object_or_404(models.Legislation, pk=kwargs["legislation_pk"])
        return super().dispatch(request, *args, **kwargs)


class AddSections(
    mixins.LoginRequiredMixin, TaxonomyFormMixin, SectionFormMixin, CreateView
):
    template_name = "legislation/sections/add.html"
    model = models.LegislationSection
    form_class = forms.SectionForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        last_section = (
            self.law.sections.order_by("pk").last() if self.law.sections else None
        )
        starting_page = last_section.legislation_page if last_section else 1

        context.update(
            {
                "law": self.law,
                "starting_page": starting_page,
                "last_section": last_section,
                "add_section": True,
                "tag_groups": [
                    TagGroupRender(tag_group)
                    for tag_group in models.TaxonomyTagGroup.objects.all()
                ],
                "classifications": models.TaxonomyClassification.objects.filter(
                    level=0
                ).order_by("code"),
            }
        )
        return context

    def form_valid(self, form):
        section = form.save()
        if section.parent:
            section.code_order = "{}.{}".format(section.parent.code_order, section.parent.get_children().count())
        else:
            section.code_order = section.legislation.sections.filter(parent=None).count()

        section.save()
        if "save-and-continue-btn" in self.request.POST:
            return HttpResponseRedirect(
                reverse(
                    "lcc:legislation:sections:add",
                    kwargs={"legislation_pk": section.legislation.pk},
                )
            )
        if "save-btn" in self.request.POST:
            return HttpResponseRedirect(
                reverse(
                    "lcc:legislation:sections:view",
                    kwargs={"legislation_pk": section.legislation.pk},
                )
            )


class SectionsList(DetailView):
    template_name = "legislation/sections/list.html"
    context_object_name = "law"
    model = models.Legislation
    pk_url_kwarg = "legislation_pk"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        class Array(Subquery):
            template = 'ARRAY(%(subquery)s)'
            output_field = ArrayField(base_field=IntegerField())

        desc = models.LegislationSection.objects.filter(
            tree_id=OuterRef('tree_id')
        ).exclude(level=0).values('pk')
        sections = models.LegislationSection.objects.filter(
            legislation=self.object
        ).annotate(descendants=Array(desc))

        child = self.request.GET.get('child', None)
        if child:
            child = int(child)
        context['child'] = child
        context["sections"] = cache_tree_children(
            sections
            .extra(
                select={
                    "code_order_fix": "string_to_array(code_order, '.')::int[]",
                },
            )
            .order_by("code_order_fix")
        )
        return context


class EditSections(
    mixins.LoginRequiredMixin, TaxonomyFormMixin, SectionFormMixin, UpdateView
):
    template_name = "legislation/sections/edit.html"
    model = models.LegislationSection
    context_object_name = "section"
    form_class = forms.SectionForm
    pk_url_kwarg = "section_pk"

    def get_object(self, **kwargs):
        return get_object_or_404(
            models.LegislationSection,
            pk=self.kwargs["section_pk"],
            legislation__pk=self.kwargs["legislation_pk"],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        section = self.get_object()
        context.update(
            {
                "starting_page": section.legislation_page,
                "law": section.legislation,
                "selected_tags": [tag.name for tag in section.tags.all()],
                "selected_classifications": [
                    classification.name
                    for classification in section.classifications.all()
                ],
                "tag_groups": [
                    TagGroupRender(tag_group)
                    for tag_group in models.TaxonomyTagGroup.objects.all()
                ],
                "classifications": models.TaxonomyClassification.objects.filter(
                    level=0
                ).order_by("code"),
            }
        )
        return context

    def form_invalid(self, form):
        print(form.errors)
        section = self.get_object()
        return HttpResponseRedirect(
            reverse(
                "lcc:legislation:sections:edit",
                kwargs={
                    "legislation_pk": section.legislation.pk,
                    "section_pk": section.pk,
                },
            )
        )

    def form_valid(self, form):
        section = form.save()

        return HttpResponseRedirect(
            reverse(
                "lcc:legislation:sections:view",
                kwargs={"legislation_pk": section.legislation.pk},
            )
        )


class DeleteSection(mixins.LoginRequiredMixin, DeleteView):
    model = models.LegislationSection
    pk_url_kwarg = "section_pk"

    def get_success_url(self, **kwargs):
        legislation_pk = self.kwargs["legislation_pk"]
        return reverse(
            "lcc:legislation:sections:view", kwargs={"legislation_pk": legislation_pk}
        )

    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)
