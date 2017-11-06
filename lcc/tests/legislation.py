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
        import ipdb; ipdb.set_trace()
        call_command('search_index', '--rebuild', '-f')

    def test_html(self):
        """
        Makes sure HTML has minimum required elements for page to work.
        """
        c = Client()
        response = c.get('/legislation/')
        self.assertContains(response, '<div id="laws"')

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

    def test_classification_filtering(self):
        # The following are the ids of all Legislations who are classified with
        # at least one "Dedicated climate laws and governance" classification.
        expected_legislation_ids = [1, 2, 4, 5, 6, 7, 8, 10]

        c = Client()
        response = c.get(
            '/legislation/', {'partial': True, 'classifications[]': '1'})

        returned_legislation_ids = sorted(
            [law.id for law in response.context['laws']])

        self.assertEqual(expected_legislation_ids, returned_legislation_ids)
