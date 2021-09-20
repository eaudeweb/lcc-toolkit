from lcc.models import (
    Answer,
    Assessment,
    Country,
    Question,
    TaxonomyClassification,
    TaxonomyTag,
    Gap,
    Legislation,
    LegislationSection,
)
from rest_framework import serializers


class QuestionAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ("id", "value")


class QuestionSerializer(serializers.ModelSerializer):
    children_yes = serializers.SerializerMethodField("_get_children_yes")
    children_no = serializers.SerializerMethodField("_get_children_no")
    children = serializers.SerializerMethodField("_get_children")
    answer = serializers.SerializerMethodField("_get_answer")
    details = serializers.SerializerMethodField("_get_details")

    class Meta:
        model = Question
        fields = (
            "id",
            "text",
            "order",
            "answer",
            "details",
            "children_yes",
            "children_no",
            "children",
        )

    def _get_answer(self, obj):
        assessment_pk = self.context.get("assessment_pk")
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
            serializer = QuestionSerializer(query, context=self.context, many=True)
            return serializer.data

    def _get_children_no(self, obj):
        query = obj.get_children().filter(parent_answer=False)
        if query:
            serializer = QuestionSerializer(query, context=self.context, many=True)
            return serializer.data

    def _get_children(self, obj):
        query = obj.get_children().filter(parent_answer=None)
        if query:
            serializer = QuestionSerializer(query, context=self.context, many=True)
            return serializer.data

    def _get_details(self, obj):
        if obj.classification:
            return obj.classification.details
        return ""


class SimpleClassificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxonomyClassification
        fields = ("id", "name", "details")


class ClassificationSerializer(serializers.ModelSerializer):
    second_level = serializers.SerializerMethodField("_get_second_level")

    class Meta:
        model = TaxonomyClassification
        fields = ("id", "name", "details", "second_level")

    def _get_second_level(self, obj):

        query = obj.get_children().order_by("code")
        new_query = query
        for second_level in query:
            if not Question.objects.filter(classification=second_level):
                new_query = new_query.exclude(pk=second_level.pk)

        if new_query:
            return SimpleClassificationSerializer(new_query, many=True).data


class TagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxonomyTag
        fields = ("id", "name")


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = "__all__"


class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = ("id", "user", "country", "country_name", "country_iso")


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ("iso", "name")


# Serializers for assessment results
class GapSerializer(serializers.ModelSerializer):
    classifications = SimpleClassificationSerializer(many=True)
    tags = TagsSerializer(many=True)

    class Meta:
        model = Gap
        fields = ("classifications", "tags")


class LegislationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Legislation
        fields = ("id", "title", "year", "country_name", "country_iso")


class GapSectionSerializer(serializers.ModelSerializer):
    legislation = LegislationSerializer()

    class Meta:
        model = LegislationSection
        fields = ("id", "code", "text", "legislation")


class ResultQuestionSerializer(serializers.ModelSerializer):
    sections = GapSectionSerializer(many=True)
    gap = GapSerializer()
    answer = serializers.BooleanField()

    class Meta:
        model = Question
        fields = ("id", "text", "answer", "gap", "sections")


class SubCategorySerializer(serializers.ModelSerializer):
    questions = ResultQuestionSerializer(many=True)

    class Meta:
        model = TaxonomyClassification
        fields = ("id", "name", "questions")


class RootCategorySerializer(serializers.ModelSerializer):
    categories = SubCategorySerializer(many=True)

    class Meta:
        model = TaxonomyClassification
        fields = ("id", "name", "categories")


class AssessmentResultSerializer(serializers.ModelSerializer):
    categories = RootCategorySerializer(many=True)

    class Meta:
        model = Assessment
        fields = ("categories",)
