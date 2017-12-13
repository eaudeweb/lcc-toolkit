import os
import shutil

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.conf import settings

from lcc.models import Legislation


class LegislationExplorer(TestCase):
    fixtures = [
        'Countries.json',
        'Gaps.json',
        'Questions.json',
        'TaxonomyClassification.json',
        'TaxonomyTag.json',
        'TaxonomyTagGroup.json',
        'Legislation.json',
    ]

    def setUp(self):
        with open(os.devnull, 'w') as f:
            call_command('search_index', '--rebuild', '-f', stdout=f)

    @override_settings(LAWS_PER_PAGE=2)
    def test_html(self):
        """
        Makes sure HTML has minimum required elements for page to work.
        """
        c = Client()
        response = c.get('/legislation/')
        self.assertContains(response, '<div id="laws"')
        self.assertContains(response, '<ul class="pagination">')
        self.assertContains(response, '<li class="page-item">')

    def test_best_fields_and_highlights(self):
        """
        Test that full-text search respects best_fields logic and highlights
        matched terms. More info at:
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
            response.context['laws'][0].highlighted_title(),
            "Keeping pets healthy"
        )
        self.assertEqual(
            response.context['laws'][0].highlighted_abstract(),
            "My quick <em>brown</em> <em>fox</em> eats rabbits on a regular basis."
        )
        self.assertEqual(
            response.context['laws'][1].highlighted_title(),
            "Quick <em>brown</em> rabbits"
        )
        self.assertEqual(
            response.context['laws'][1].highlighted_abstract(),
            "<em>Brown</em> rabbits are commonly seen."
        )

    def test_pdf_highlights(self):
        pdf_file = open('lcc/tests/files/snake.pdf', 'rb')
        law = Legislation.objects.create(
            title="Brazilian snakes",
            abstract="Brazilian snakes must be protected",
            country_id="BRA",
            pdf_file=InMemoryUploadedFile(
                pdf_file, None, 'snake.pdf', 'application/pdf', None, None)
        )
        law.save_pdf_pages()
        c = Client()
        response = c.get('/legislation/', {'partial': True, 'q': "jararaca"})
        self.assertIn(
            '<em>jararaca</em>',
            response.context['laws'][0].highlighted_pdf_text(),
        )

    def test_article_text_highlights(self):

        Legislation.objects.first().articles.create(
            text="Brown rabbits are commonly seen.",
            legislation_page=1,
            code="Art. I"
        )

        c = Client()
        response = c.get('/legislation/', {'partial': True, 'q': "rabbits"})

        self.assertEqual(
            response.context['laws'][0].highlighted_articles()[0]['text'],
            "Brown <em>rabbits</em> are commonly seen."
        )

    def test_classification_filtering(self):

        classification_ids = ['1', '74']  # Arbitrary level 0 classifications

        c = Client()
        response = c.get(
            '/legislation/',
            {'partial': True, 'classifications[]': classification_ids}
        )

        expected_law_classifications_list = [
            [1, 74, 93],
            [1, 45, 74, 93],
            [1, 93],
            [1, 45, 74, 93],
            [1, 45, 74, 93],
            [74],
            [1, 93],
            [45, 74, 93]
        ]
        # TODO: Intentionally define an order to be returned. Currently this
        # order is accidental, a result of ES's default scoring algorithms. This
        # should be fixed. Until then, if this test breaks because the order
        # changed, you can just change the order of the list above so the test
        # passes because it has no important meaning.

        returned_law_classifications_list = [
            list(law.classifications.values_list('id', flat=True))
            for law in response.context['laws']
        ]

        self.assertEqual(
            expected_law_classifications_list,
            returned_law_classifications_list
        )

    def test_article_classification_filtering(self):

        classification_ids = ['3', '9']  # Arbitrary non-0 level classifications

        laws = list(Legislation.objects.all())
        law1, law2 = laws[:2]  # Get two arbitrary laws

        article1 = law1.articles.create(
            text="Some text",
            legislation_page=1,
            code="Art. I"
        )

        article1.classifications.add(3)

        article2 = law2.articles.create(
            text="Some other text",
            legislation_page=1,
            code="Art. I"
        )

        article2.classifications.add(9)

        c = Client()
        response = c.get(
            '/legislation/',
            {'partial': True, 'classifications[]': classification_ids}
        )

        expected_laws = [law1, law2]

        returned_laws = response.context['laws'].object_list

        self.assertEqual(expected_laws, returned_laws)

    def test_full_text_classification_search(self):

        q = 'climate renewable'  # Arbitrary words found in classification names

        c = Client()
        response = c.get('/legislation/', {'partial': True, 'q': q})

        returned_laws = response.context['laws'].object_list

        self.assertEqual(len(returned_laws), 8)
        self.assertIn(
            'Dedicated <em>climate</em> laws and governance',
            returned_laws[0].highlighted_classifications()
        )
        self.assertIn(
            'Energy production and <em>renewable</em> energy laws',
            returned_laws[0].highlighted_classifications()
        )

    def test_tag_filtering(self):

        tag_ids = ['1', '2']  # Arbitrary tags

        c = Client()
        response = c.get(
            '/legislation/',
            {'partial': True, 'tags[]': tag_ids}
        )

        expected_law_tag_list = [
            (4, [1]),
            (8, [1, 2, 5, 6]),
            (6, [1, 2, 3, 4, 5, 6]),
            (10, [1, 2, 3, 4, 5, 6]),
            (5, [1, 2, 4, 5, 6]),
            (2, [2, 4]),
            (7, [1, 2, 3, 5, 6]),
            (1, [1, 2, 3, 4, 5, 6]),
            (3, [2, 3, 5])
        ]
        # TODO: Intentionally define an order to be returned. Currently this
        # order is accidental, a result of ES's default scoring algorithms. This
        # should be fixed. Until then, if this test breaks because the order
        # changed, you can just change the order of the list above so the test
        # passes because it has no important meaning.

        returned_law_tag_list = [
            (law.id, list(law.tags.values_list('id', flat=True)))
            for law in response.context['laws']
        ]
        self.assertEqual(
            expected_law_tag_list,
            returned_law_tag_list
        )

    def test_article_tag_filtering(self):

        tag_ids = ['3', '4']  # Arbitrary tags

        # Get two laws that are NOT tagged with those tags
        law1, law2 = Legislation.objects.filter(pk__in=[4, 8])

        # Add articles to them and tag the articles with those tags
        article1 = law1.articles.create(
            text="Some text",
            legislation_page=1,
            code="Art. I"
        )

        article1.tags.add(3)

        article2 = law2.articles.create(
            text="Some other text",
            legislation_page=1,
            code="Art. I"
        )

        article2.tags.add(4)

        c = Client()
        response = c.get(
            '/legislation/',
            {'partial': True, 'tags[]': tag_ids}
        )

        expected_law_tag_list = [
            (6, [1, 2, 3, 4, 5, 6]),
            (2, [2, 4]),
            (10, [1, 2, 3, 4, 5, 6]),
            (8, [1, 2, 5, 6]),  # Found inside article
            (4, [1]),  # Found inside article
            (1, [1, 2, 3, 4, 5, 6]),
            (9, [4]),
            (3, [2, 3, 5]),
            (5, [1, 2, 4, 5, 6]),
            (7, [1, 2, 3, 5, 6])
        ]
        # TODO: Intentionally define an order to be returned. Currently this
        # order is accidental, a result of ES's default scoring algorithms. This
        # should be fixed. Until then, if this test breaks because the order
        # changed, you can just change the order of the list above so the test
        # passes because it has no important meaning.

        returned_law_tag_list = [
            (law.id, list(law.tags.values_list('id', flat=True)))
            for law in response.context['laws']
        ]
        self.assertEqual(expected_law_tag_list, returned_law_tag_list)

    def test_full_text_tag_search(self):

        q = 'enforcement'  # Arbitrary word found in one of the tag names

        c = Client()
        response = c.get('/legislation/', {'partial': True, 'q': q})

        returned_laws = response.context['laws'].object_list
        self.assertEqual(len(returned_laws), 7)
        self.assertIn(
            'Provisions for non-compliance and <em>enforcement</em>',
            returned_laws[0].highlighted_tags()
        )

    def test_country_filtering(self):

        iso_codes = ['MMR', 'PAN']  # Arbitrary country ids

        c = Client()
        response = c.get(
            '/legislation/',
            {'partial': True, 'countries[]': iso_codes}
        )

        expected_law_ids = [4, 6]
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

    def test_year_range_filtering(self):

        # Arbitrary years
        from_year = 1950
        to_year = 2005

        c = Client()
        response = c.get(
            '/legislation/',
            {'partial': True, 'from_year': from_year, 'to_year': to_year}
        )
        expected_law_ids = [6, 9, 10]
        returned_law_ids = [law.id for law in response.context['laws']]

        self.assertEqual(expected_law_ids, returned_law_ids)

    @override_settings(LAWS_PER_PAGE=2)
    def test_pagination(self):

        c = Client()

        # Get all 10 legislations
        response = c.get('/legislation/')

        # Defaults to first page
        self.assertEqual(len(response.context['laws']), 2)
        self.assertEqual(response.context['laws'].number, 1)

        # Get second page
        response = c.get(
            '/legislation/',
            {'partial': True, 'page': 2}
        )

        # Returns second page
        self.assertEqual(len(response.context['laws']), 2)
        self.assertEqual(response.context['laws'].number, 2)

        # Get 6 filtered legislations
        law_types = ['Law', 'Constitution']  # Law types that return 6 results
        response = c.get(
            '/legislation/',
            {'partial': True, 'law_types[]': law_types}
        )

        # Defaults to first page
        self.assertEqual(len(response.context['laws']), 2)
        self.assertEqual(response.context['laws'].number, 1)

        # Get second page
        response = c.get(
            '/legislation/',
            {'partial': True, 'law_types[]': law_types, 'page': 2}
        )
        self.assertEqual(len(response.context['laws']), 2)
        self.assertEqual(response.context['laws'].number, 2)

        # Get 1 filtered legislation
        country_iso = 'MMR'  # Country id that returns only one result
        response = c.get(
            '/legislation/',
            {'partial': True, 'countries[]': [country_iso]}
        )

        self.assertEqual(len(response.context['laws']), 1)
        self.assertEqual(response.context['laws'].number, 1)

        # Try to get second page (doesn't exist)
        response = c.get(
            '/legislation/',
            {'partial': True, 'countries[]': [country_iso], 'page': 2}
        )

        # Returns last existing page
        self.assertEqual(len(response.context['laws']), 1)
        self.assertEqual(response.context['laws'].number, 1)

    def tearDown(self):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
