from lcctoolkit.mainapp.models import Question

from rest_framework import serializers


class QuestionSerializer(serializers.ModelSerializer):
    children_yes = serializers.SerializerMethodField('_get_children_yes')
    children_no = serializers.SerializerMethodField('_get_children_no')

    class Meta:
        model = Question
        fields = ("id", "text", "order",
                  "children_yes", "children_no")

    def _get_children_yes(self, obj):
        query = obj.get_children().filter(parent_answer=True)
        if query:
            serializer = QuestionSerializer(query, many=True)
            return serializer.data

    def _get_children_no(self, obj):
        query = obj.get_children().filter(parent_answer=False)
        if query:
            serializer = QuestionSerializer(query, many=True)
            return serializer.data
