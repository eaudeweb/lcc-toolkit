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
        c = Client()
        response = c.get('/legislation/', {'partial': True, 'q': "Brown fox"})
        self.assertEqual(
            response.context['laws'][0].title, "Keeping pets healthy")
        self.assertEqual(
            response.context['laws'][1].title, "Quick brown rabbits")

    def test_classification_filtering(self):

        classification_ids = ['1', '74']  # Arbitrary level 0 classifications

        c = Client()
        response = c.get(
            '/legislation/',
            {'partial': True, 'classifications[]': classification_ids}
        )

        expected_law_classifications_list = [
            [1, 45, 74, 93],
            [1, 74, 93],
            [1, 45, 74, 93],
            [1, 45, 74, 93],
            [1, 93],
            [74],
            [1, 93],
            [45, 74, 93]
        ]  # Note that documents that have both classifications score higher

        returned_law_classifications_list = [
            list(law.classifications.values_list('id', flat=True))
            for law in response.context['laws']
        ]

        self.assertEqual(
            expected_law_classifications_list,
            returned_law_classifications_list
        )

    def test_tag_filtering(self):

        tag_ids = ['1', '2']  # Arbitrary tags

        c = Client()
        response = c.get(
            '/legislation/',
            {'partial': True, 'tags[]': tag_ids}
        )

        expected_law_tag_list = [
            [1, 2, 3, 4, 5, 6],
            [1, 2, 5, 6],
            [1, 2, 4, 5, 6],
            [1, 2, 3, 4, 5, 6],
            [1, 2, 3, 5, 6],
            [1, 2, 3, 4, 5, 6],
            [2, 4],
            [1],
            [2, 3, 5]
        ]  # Note that documents that have both tags score higher

        returned_law_tag_list = [
            list(law.tags.values_list('id', flat=True))
            for law in response.context['laws']
        ]

        self.assertEqual(
            expected_law_tag_list,
            returned_law_tag_list
        )

    def test_country_filtering(self):

        country_iso = 'MMR'  # Arbitrary country id

        c = Client()
        response = c.get(
            '/legislation/',
            {'partial': True, 'country': country_iso}
        )

        expected_law_ids = [4]
        returned_law_ids = [law.id for law in response.context['laws']]

        self.assertEqual(expected_law_ids, returned_law_ids)

    def test_law_type_filtering(self):

        law_types = ['Law', 'Constitution']  # Arbitrary law types

        c = Client()
        response = c.get(
            '/legislation/',
            {'partial': True, 'law_types[]': law_types}
        )

        expected_law_ids = [1, 2, 3, 5, 6, 10]
        returned_law_ids = [law.id for law in response.context['laws']]

        self.assertEqual(expected_law_ids, returned_law_ids)
