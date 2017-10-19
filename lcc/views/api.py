from rest_framework import generics

from lcc import models, serializers


class QuestionViewSet(generics.ListAPIView):
    serializer_class = serializers.QuestionSerializer

    def get_queryset(self):
        category = self.kwargs['category_pk']
        return models.Question.objects.filter(level=0, classification=category)


class ClassificationViewSet(generics.ListAPIView):
    queryset = models.TaxonomyClassification.objects.filter(level=0).order_by('code')
    serializer_class = serializers.ClassificationSerializer


class AnswerList(generics.ListCreateAPIView):
    queryset = models.Answer.objects.all()
    serializer_class = serializers.AnswerSerializer


class AnswerDetail(generics.RetrieveUpdateAPIView):
    queryset = models.Answer.objects.all()
    serializer_class = serializers.AnswerSerializer
