import re

from django_elasticsearch_dsl import DocType, Index, fields
from django.conf import settings
from django.core.exceptions import ValidationError

from lcc.models import (
    Legislation, LegislationArticle, TaxonomyClassification, TaxonomyTag)

CONN = settings.TAXONOMY_CONNECTOR

# Name of the Elasticsearch index
legislation = Index('legislations')


@legislation.doc_type
class LegislationDocument(DocType):

    classifications = fields.TextField(term_vector='with_positions_offsets')

    article_classifications = fields.TextField(term_vector='with_positions_offsets')

    tags = fields.TextField(term_vector='with_positions_offsets')

    article_tags = fields.TextField(term_vector='with_positions_offsets')

    country = fields.KeywordField()

    law_type = fields.KeywordField()

    pdf_text = fields.TextField()

    year_mentions = fields.ListField(fields.IntegerField())

    articles = fields.NestedField(properties={
        'pk': fields.IntegerField(),
        'code': fields.KeywordField(),
        'text': fields.TextField(),
        'classifications_text': fields.TextField(
            term_vector='with_positions_offsets'
        ),
        'parent_classifications': fields.TextField(
            term_vector='with_positions_offsets'
        ),
        'tags_text': fields.TextField(
            term_vector='with_positions_offsets'
        ),
        'parent_tags': fields.TextField(
            term_vector='with_positions_offsets'
        )
    })

    def prepare_classifications(self, instance):
        classification_names = instance.classifications.all().values_list(
            'name', flat=True)
        if CONN in ''.join(classification_names):
            raise ValidationError(
                "Classification names must not include the character "
                "'{}'.".format(CONN)
            )
        return CONN.join(classification_names)

    def prepare_article_classifications(self, instance):
        classification_names = {
            cl.name for cl in [
                item for sublist in [
                    article.classifications.all()
                    for article in instance.articles.all()
                ]
                for item in sublist
            ]
        }
        if CONN in ''.join(classification_names):
            raise ValidationError(
                "Classification names must not include the character "
                "'{}'.".format(CONN)
            )
        return CONN.join(classification_names)

    def prepare_tags(self, instance):
        tag_names = instance.tags.all().values_list('name', flat=True)
        if CONN in ''.join(tag_names):
            raise ValidationError(
                "Tag names must not include the character '{}'.".format(CONN))
        return CONN.join(tag_names)

    def prepare_article_tags(self, instance):
        tag_names = {
            tag.name for tag in
            [
                item for sublist in
                [article.tags.all() for article in instance.articles.all()]
                for item in sublist
            ]
        }
        if CONN in ''.join(tag_names):
            raise ValidationError(
                "Tag names must not include the character '{}'.".format(CONN))
        return CONN.join(tag_names)

    def prepare_country(self, instance):
        return instance.country.iso

    def prepare_pdf_text(self, instance):
        return '\n\n'.join([page.page_text for page in instance.pages.all()])

    def prepare_year_mentions(self, instance):
        return [
            int(year) for year in
            re.findall('\d{4}', instance.year_mention or '')
            if int(year) >= settings.MIN_YEAR and
            int(year) <= settings.MAX_YEAR
        ]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, LegislationArticle):
            return related_instance.legislation
        else:  # it's a TaxonomyClassification or TaxonomyTag
            return related_instance.legislation_set.all()

    class Meta:
        model = Legislation  # The model associated with this DocType

        # The fields of the model to be indexed in Elasticsearch
        fields = [
            'id',
            'title',
            'abstract',
            'year',
            'year_amendment',
        ]

        related_models = [
            LegislationArticle, TaxonomyClassification, TaxonomyTag]
