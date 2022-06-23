from collections import defaultdict

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import mixins
from django import views

from lcc import models


class TagGroupRender:
    def __init__(self, tag_group):
        self.name = tag_group.name
        self.pk = tag_group.pk
        self.tags = [
            {"name": tag.name, "pk": tag.pk}
            for tag in models.TaxonomyTag.objects.filter(group=tag_group)
        ]


class TaxonomyFormMixin:
    def get_form_kwargs(self):
        kwargs = {
            "initial": self.get_initial(),
            "prefix": self.get_prefix(),
        }

        if self.request.method in ("POST", "PUT"):
            post_data = self.request.POST
            kwargs["data"] = defaultdict(list)
            for field in post_data.keys():
                if "classification" in field:
                    kwargs["data"]["classifications"].append(int(field.split("_")[1]))
                elif "tag" in field:
                    kwargs["data"]["tags"].append(int(field.split("_")[1]))
                else:
                    kwargs["data"][field] = post_data[field]
            kwargs["files"] = self.request.FILES
            for file in kwargs["files"].keys():
                kwargs["data"][file + "_name"] = kwargs["files"][file].name

        if hasattr(self, "object"):
            kwargs.update({"instance": self.object})
        return kwargs


class HomePageView(views.generic.TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        static_page = models.StaticPage.objects.filter(
            page=models.StaticPage.HOMEPAGE
        ).first()

        context["static_page"] = static_page

        return context


class AboutUsView(views.generic.TemplateView):
    template_name = "about_us.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        static_page = models.StaticPage.objects.filter(
            page=models.StaticPage.ABOUT_US
        ).first()

        context["static_page"] = static_page

        return context


class LessonsLearnedView(mixins.LoginRequiredMixin, views.generic.TemplateView):
    template_name = "lessons_learned.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        static_page = models.StaticPage.objects.filter(
            page=models.StaticPage.LESSONS_LEARNED
        ).first()

        context["static_page"] = static_page

        return context
