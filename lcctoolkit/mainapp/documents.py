from django_elasticsearch_dsl import DocType, Index
from .models import Legislation

# Name of the Elasticsearch index
legislation = Index('legislations')


@legislation.doc_type
class LegislationDocument(DocType):
    class Meta:
        model = Legislation  # The model associated with this DocType

        # The fields of the model you want to be indexed in Elasticsearch
        fields = [
            'title',
            'abstract',
            # TODO: 'pdf_file'
        ]
