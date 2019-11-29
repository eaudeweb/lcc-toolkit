from rest_framework import generics

from django.db.models import IntegerField
from django.db.models.functions import Cast

from lcc import models, serializers
from lcc.views.country import CountryMetadataFiltering

class AssessmentSuggestionsMixin(CountryMetadataFiltering):
    def get_assessment_object(self, assessment):
        answers = models.Answer.objects.get_assessment_answers(assessment.pk)
        category_ids = {a.category_id for a in answers}
        sub_categories = models.TaxonomyClassification.objects.filter(
            pk__in=category_ids
        )
        root_categories = models.TaxonomyClassification.objects.filter(
            pk__in=[cat.parent_id for cat in sub_categories]
        )

        for root in root_categories:
            root.categories = [
                sub for sub in sub_categories
                if sub.parent_id == root.id
            ]

        gap_ids = []

        for a in answers:
            q = a.question
            q.answer = a.value

            gap_ids.append(a.gap_id)

            category = next(
                cat for cat in sub_categories
                if cat.id == a.category_id
            )
            try:
                cat_qs = category.questions
            except AttributeError:
                category.questions = []
                cat_qs = category.questions

            cat_qs.append(q)

        gaps = models.Gap.objects.filter(id__in=gap_ids).prefetch_related(
            'classifications', 'tags')

        for a in answers:
            a.question.gap = next(
                gap for gap in gaps
                if gap.id == a.gap_id
            )
        assessment.categories = root_categories
        similar_countries = self.filter_countries(self.request, country=None)
        articles = models.LegislationArticle.objects.get_articles_for_gaps(
            gap_ids, similar_countries)

        for a in answers:
            a.question.articles = [
                article for article in articles
                if a.question.gap.id == article.gap_id
            ]

        return assessment


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
    serializer_class = serializers.ClassificationSerializer

    def get_queryset(self):
        queryset = models.TaxonomyClassification.objects.filter(
            level=0
        ).annotate(
            code_as_int=Cast('code', output_field=IntegerField())
        ).order_by('code_as_int')

        new_queryset = queryset
        for top_level in queryset:
            flag = False
            for second_level in top_level.get_children().order_by('code'):
                if models.Question.objects.filter(classification=second_level):
                    flag = True
            if not flag:
                new_queryset = new_queryset.exclude(pk=top_level.pk)

        return new_queryset


class AnswerList(generics.ListCreateAPIView):
    queryset = models.Answer.objects.all()
    serializer_class = serializers.AnswerSerializer


class AnswerDetail(generics.RetrieveUpdateAPIView):
    queryset = models.Answer.objects.all()
    serializer_class = serializers.AnswerSerializer


class AssessmentList(generics.ListCreateAPIView):
    queryset = models.Assessment.objects.all()
    serializer_class = serializers.AssessmentSerializer

    def get_queryset(self):
        return models.Assessment.objects.filter(user=self.request.user)


class CountryViewSet(generics.ListAPIView):
    queryset = models.Country.objects.all()
    serializer_class = serializers.CountrySerializer


class AssessmentResults(AssessmentSuggestionsMixin, generics.RetrieveAPIView):
    serializer_class = serializers.AssessmentResultSerializer

    def get_queryset(self):
        return models.Assessment.objects.filter(
            pk=self.kwargs['pk'],
            user=self.request.user,
        )

    def get_object(self):
        # decorate the assessment with... some stuff
        assessment = super().get_object()
        return self.get_assessment_object(assessment)
