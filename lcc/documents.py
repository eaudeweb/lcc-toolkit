from django_elasticsearch_dsl import DocType, Index, fields
from lcc.models import Legislation

# Name of the Elasticsearch index
legislation = Index('legislations')


@legislation.doc_type
class LegislationDocument(DocType):

    classifications = fields.ListField(fields.IntegerField())

    tags = fields.ListField(fields.IntegerField())

    country = fields.KeywordField()

    def prepare_classifications(self, instance):
        return list(instance.classifications.all().values_list('id', flat=True))

    def prepare_tags(self, instance):
        return list(instance.tags.all().values_list('id', flat=True))

    def prepare_country(self, instance):
        return instance.country.iso

    class Meta:
        model = Legislation  # The model associated with this DocType

        # The fields of the model you want to be indexed in Elasticsearch
        fields = [
            'title',
            'abstract',
            'law_type',
            # TODO: 'pdf_file'
        ]
