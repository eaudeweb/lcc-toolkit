from lcc.models import (
    Answer, Assessment, Country, Question, TaxonomyClassification
)
from rest_framework import serializers


class QuestionAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ("id", "value")


class QuestionSerializer(serializers.ModelSerializer):
    children_yes = serializers.SerializerMethodField('_get_children_yes')
    children_no = serializers.SerializerMethodField('_get_children_no')
    children = serializers.SerializerMethodField('_get_children')
    answer = serializers.SerializerMethodField('_get_answer')

    class Meta:
        model = Question
        fields = ("id", "text", "order", "answer",
                  "children_yes", "children_no", "children")

    def _get_answer(self, obj):
        assessment_pk = self.context.get('assessment_pk')
        query = None

        if assessment_pk:
            query = Answer.objects.filter(
                question=obj, assessment__pk=assessment_pk
            ).first()

        if query:
            serializer = QuestionAnswerSerializer(query)
            return serializer.data

    def _get_children_yes(self, obj):
        query = obj.get_children().filter(parent_answer=True)
        if query:
            serializer = QuestionSerializer(
                query, context=self.context, many=True)
            return serializer.data

    def _get_children_no(self, obj):
        query = obj.get_children().filter(parent_answer=False)
        if query:
            serializer = QuestionSerializer(
                query, context=self.context, many=True)
            return serializer.data

    def _get_children(self, obj):
        query = obj.get_children().filter(parent_answer=None)
        if query:
            serializer = QuestionSerializer(
                query, context=self.context, many=True)
            return serializer.data


class SecondClassificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxonomyClassification
        fields = ("id", "name")


class ClassificationSerializer(serializers.ModelSerializer):
    second_level = serializers.SerializerMethodField('_get_second_level')

    class Meta:
        model = TaxonomyClassification
        fields = ("id", "name", "second_level")

    def _get_second_level(self, obj):
        query = obj.get_children().order_by('code')
        if query:
            return SecondClassificationSerializer(query, many=True).data


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = '__all__'


class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = ("user", "country", "country_name")


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ("iso", "name")
