from django.contrib.auth import mixins
from django.views.generic import TemplateView
from lcc.views.api import AssessmentResults
from rest_framework.response import Response
from django.http import HttpResponse
from rest_framework.renderers import TemplateHTMLRenderer
from lcc import serializers, utils


class LegalAssessment(mixins.LoginRequiredMixin, TemplateView):
    template_name = "assessment.html"


class LegalAssessmentResults(mixins.LoginRequiredMixin, TemplateView):
    template_name = "assessment_results.html"


class LegalAssessmentResultsPDF(AssessmentResults):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'profile_list.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        results = serializers.AssessmentResultSerializer(self.object)

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
            'host': request.META['HTTP_HOST'],
            'categories': top_categories,
            'areas': areas,
            'law_suggestions': suggestions
        }

        # For html version, comment lines 44-45 and uncomment line 46
        pdf = utils.render_to_pdf('results_pdf.html', context)
        return HttpResponse(pdf, content_type='application/pdf')
        # return Response(context, template_name='results_pdf.html')
