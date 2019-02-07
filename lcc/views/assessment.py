from django.contrib.auth import mixins
from django.views.generic import TemplateView, View
from lcc.views.api import AssessmentSuggestionsMixin
from lcc import serializers
from lcc.models import Assessment

from django.template.loader import get_template
from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings

from weasyprint import HTML, CSS


class LegalAssessment(mixins.LoginRequiredMixin, TemplateView):
    template_name = "assessment.html"


class LegalAssessmentResults(mixins.LoginRequiredMixin, TemplateView):
    template_name = "assessment_results.html"


class LegalAssessmentResultsPDF(View, AssessmentSuggestionsMixin):
    template_name = 'results_pdf.html'

    def get(self, request, *args, **kwargs):

        assessment = Assessment.objects.get(pk=kwargs['pk'])
        results = serializers.AssessmentResultSerializer(
            self.get_assessment_object(assessment)
        )

        top_categories = len(results.data['categories'])
        areas = 0
        suggestions = 0
        for category in results.data['categories']:
            for subcategory in category['categories']:
                areas += len(subcategory['questions'])
                for question in subcategory['questions']:
                    suggestions += len(question['articles'])

        context = {
            'results': results.data,
            'host': settings.DOMAIN,
            'categories': top_categories,
            'areas': areas,
            'law_suggestions': suggestions,
            'assessment_country_iso': assessment.country_iso,
            'assessment_country_name': assessment.country_name,
            'request': request
        }

        pdf_name = 'leagal_assessment_for_{}_by_{}.pdf'.format(
            assessment.country_name, request.user.username
        )

        html_template = get_template(self.template_name)
        rendered_html = html_template.render(context).encode(encoding="UTF-8")
        pdf_file = HTML(
            string=rendered_html).write_pdf(
            stylesheets=[
                CSS(settings.STATIC_ROOT + '/css/download_results.css')
            ]
        )

        http_response = HttpResponse(pdf_file, content_type='application/pdf')
        http_response['Content-Disposition'] = 'attachment; filename="{}"'.format(pdf_name)

        return http_response
        # return render(request, self.template_name, context)
