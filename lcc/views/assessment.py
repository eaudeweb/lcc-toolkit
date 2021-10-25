from django.conf import settings
from django.contrib.auth import mixins
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import get_template
from django.views.generic import TemplateView, View

from lcc import serializers
from lcc.models import Assessment, Region, SubRegion, LegalSystem
from lcc.views.api import AssessmentSuggestionsMixin
from lcc.views.country import (
    POP_RANGES,
    HDI_RANGES,
    GDP_RANGES,
    GHG_LUCF,
    GHG_NO_LUCF,
)

from weasyprint import HTML, CSS


class LegalAssessment(mixins.LoginRequiredMixin, TemplateView):
    template_name = "assessment.html"


class LegalAssessmentResults(mixins.LoginRequiredMixin, TemplateView):
    template_name = "assessment_results.html"

    def get_context_data(self, **kwargs):
        context_data = super(LegalAssessmentResults, self).get_context_data(**kwargs)
        regions = Region.objects.all()
        sub_regions = SubRegion.objects.all()
        legal_systems = LegalSystem.objects.all()

        context_data.update(
            {
                "regions": regions,
                "sub_regions": sub_regions,
                "legal_systems": legal_systems,
                "population": POP_RANGES,
                "hdi2015": HDI_RANGES,
                "gdp_capita": GDP_RANGES,
                "ghg_no_lucf": GHG_NO_LUCF,
                "ghg_lucf": GHG_LUCF,
            }
        )
        return context_data


class LegalAssessmentResultsPDF(AssessmentSuggestionsMixin, View):
    template_name = "results_pdf.html"

    def get(self, request, *args, **kwargs):

        assessment = Assessment.objects.get(pk=kwargs["pk"])
        results = serializers.AssessmentResultSerializer(
            self.get_assessment_object(assessment)
        )

        top_categories = len(results.data["categories"])
        areas = 0
        suggestions = 0
        for category in results.data["categories"]:
            for subcategory in category["categories"]:
                areas += len(subcategory["questions"])
                for question in subcategory["questions"]:
                    suggestions += len(question["sections"])

        context = {
            "results": results.data,
            "host": settings.DOMAIN,
            "categories": top_categories,
            "areas": areas,
            "law_suggestions": suggestions,
            "assessment_country_iso": assessment.country_iso,
            "assessment_country_name": assessment.country_name,
            "request": request,
        }

        pdf_name = "leagal_assessment_for_{}_by_{}.pdf".format(
            assessment.country_name, request.user.username
        )

        html_template = get_template(self.template_name)
        rendered_html = html_template.render(context).encode(encoding="UTF-8")
        pdf_file = HTML(string=rendered_html).write_pdf(
            stylesheets=[CSS(settings.STATIC_ROOT + "/css/download_results.css")]
        )

        http_response = HttpResponse(pdf_file, content_type="application/pdf")
        http_response["Content-Disposition"] = 'attachment; filename="{}"'.format(
            pdf_name
        )

        return http_response
        # return render(request, self.template_name, context)
