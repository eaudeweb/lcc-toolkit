from django.contrib.auth import mixins
from django.views.generic import TemplateView, View
from lcc.views.api import AssessmentResults
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
from lcc import serializers


class LegalAssessment(mixins.LoginRequiredMixin, TemplateView):
    template_name = "assessment.html"


class LegalAssessmentResults(mixins.LoginRequiredMixin, TemplateView):
    template_name = "assessment_results.html"


class LegalAssessmentResultsPDF(AssessmentResults):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'profile_list.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        result = serializers.AssessmentResultSerializer(self.object)
        return Response(
            {'result': result.data},
            template_name='results_pdf.html'
        )
