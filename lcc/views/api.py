from rest_framework import generics

from lcc import models, serializers
from django.contrib.auth import get_user_model


class QuestionViewSet(generics.ListAPIView):
    def get_serializer(self, *args, **kwargs):
        serializer_class = serializers.QuestionSerializer
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def get_queryset(self):
        category = self.kwargs['category_pk']
        return models.Question.objects.filter(level=0, classification=category)

    def get_serializer_context(self):
        assessment_pk = self.request.query_params.get('assessment_pk', None)
        if assessment_pk:
            return {'request': self.request, 'assessment_pk': assessment_pk}
        else:
            return {'request': self.request}


class ClassificationViewSet(generics.ListAPIView):
    queryset = models.TaxonomyClassification.objects.filter(
        level=0).order_by('code')
    serializer_class = serializers.ClassificationSerializer


class AnswerList(generics.ListCreateAPIView):
    queryset = models.Answer.objects.all()
    serializer_class = serializers.AnswerSerializer


class AnswerDetail(generics.RetrieveUpdateAPIView):
    queryset = models.Answer.objects.all()
    serializer_class = serializers.AnswerSerializer


class AssessmentList(generics.ListCreateAPIView):
    queryset = models.Assessment.objects.all()
    serializer_class = serializers.AssessmentSerializer


class AssessmentDetail(generics.ListAPIView):
    queryset = models.Assessment.objects.all()
    serializer_class = serializers.AssessmentSerializer

    def get_quryset(self):
        user_pk = self.kwargs['user_pk']
        user = get_user_model().objects.get(pk=user_pk)
        return models.Assessment.objects.get(user=user)


class CountryViewSet(generics.ListAPIView):
    queryset = models.Country.objects.all()
    serializer_class = serializers.CountrySerializer
