from django_elasticsearch_dsl import DocType, Index, fields
from lcc.models import Legislation

# Name of the Elasticsearch index
legislation = Index('legislations')


@legislation.doc_type
class LegislationDocument(DocType):

    classifications = fields.ListField(fields.IntegerField())

    tags = fields.ListField(fields.IntegerField())

    country = fields.KeywordField()

    law_type = fields.KeywordField(attr='law_type')

    pdf_text = fields.TextField()

    def prepare_classifications(self, instance):
        return list(instance.classifications.all().values_list('id', flat=True))

    def prepare_tags(self, instance):
        return list(instance.tags.all().values_list('id', flat=True))

    def prepare_country(self, instance):
        return instance.country.iso

    def prepare_pdf_text(self, instance):
        return '\n\n'.join([page.page_text for page in instance.pages.all()])

    class Meta:
        model = Legislation  # The model associated with this DocType

        # The fields of the model you want to be indexed in Elasticsearch
        fields = [
            'id',
            'title',
            'abstract'
        ]
