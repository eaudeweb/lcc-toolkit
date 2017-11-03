from django.core.management import call_command
from django.test import Client, TestCase
from lcc.models import Legislation


class LegislationExplorer(TestCase):

    fixtures = [
        'Countries.json',
        'CountryMetadata.json',
        'Gaps.json',
        'Questions.json',
        'TaxonomyClassification.json',
        'TaxonomyTag.json',
        'TaxonomyTagGroup.json',
        'Legislation.json',
    ]

    def setUp(self):
        Legislation.objects.create(
            title="Quick brown rabbits",
            abstract="Brown rabbits are commonly seen.",
            country_id="ROU"
        )
        Legislation.objects.create(
            title="Keeping pets healthy",
            abstract="My quick brown fox eats rabbits on a regular basis.",
            country_id="ROU"
        )

    def test_best_fields(self):
        """
        Test that full-text search respects best_fields logic. More info at:
            - https://www.elastic.co/guide/en/elasticsearch/guide/current/_best_fields.html
        """
        c = Client()
        response = c.get('/legislation/', {'partial': True, 'q': "Brown fox"})
        self.assertEqual(
            response.context['laws'][0].title, "Keeping pets healthy")
        self.assertEqual(
            response.context['laws'][1].title, "Quick brown rabbits")

    def tearDown(self):
        call_command('search_index', '--delete', '-f')
