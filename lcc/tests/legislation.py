import os
import shutil

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.conf import settings
from unittest import skip

from lcc.models import Legislation


class LegislationExplorer(TestCase):
    fixtures = [
        "Countries.json",
        "Gaps.json",
        "Questions.json",
        "TaxonomyClassification.json",
        "TaxonomyTag.json",
        "TaxonomyTagGroup.json",
        "Legislation.json",
    ]

    def setUp(self):
        os.chmod("lcc/tests/files/snake.pdf", 0o600)
        with open(os.devnull, "w") as f:
            call_command("search_index", "--rebuild", "-f", stdout=f)

    @override_settings(LAWS_PER_PAGE=2)
    def test_html(self):
        """
        Makes sure HTML has minimum required elements for page to work.
        """
        c = Client()
        response = c.get("/legislation/")
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
            country_id="ROU",
        )
        Legislation.objects.create(
            title="Keeping pets healthy",
            abstract="My quick brown fox eats rabbits on a regular basis.",
            country_id="ROU",
        )
        c = Client()
        response = c.get("/legislation/", {"q": "Brown fox"})
        self.assertEqual(
            response.context["laws"][0].highlighted_title(), "Keeping pets healthy"
        )
        self.assertEqual(
            response.context["laws"][0].highlighted_abstract(),
            "My quick <em>brown</em> <em>fox</em> eats rabbits on a regular basis.",
        )
        self.assertEqual(
            response.context["laws"][1].highlighted_title(),
            "Quick <em>brown</em> rabbits",
        )
        self.assertEqual(
            response.context["laws"][1].highlighted_abstract(),
            "<em>Brown</em> rabbits are commonly seen.",
        )

    def test_pdf_highlights(self):
        mode = int("%o" % os.stat("lcc/tests/files/snake.pdf").st_mode)
        self.assertEqual(mode, 100600)
        pdf_file = open("lcc/tests/files/snake.pdf", "rb")
        law = Legislation.objects.create(
            title="Brazilian snakes",
            abstract="Brazilian snakes must be protected",
            country_id="BRA",
            pdf_file=InMemoryUploadedFile(
                pdf_file, None, "snake.pdf", "application/pdf", None, None
            ),
        )
        mode = int("%o" % os.stat(law.pdf_file.path).st_mode)
        self.assertEqual(mode, 100644)
        law.save_pdf_pages()
        c = Client()
        response = c.get("/legislation/", {"q": "jararaca"})
        self.assertIn(
            "<em>jararaca</em>",
            response.context["laws"][0].highlighted_pdf_text(),
        )

    def test_section_text_highlights(self):

        Legislation.objects.first().sections.create(
            text="Brown rabbits are commonly seen.", legislation_page=1, code="Art. I"
        )

        c = Client()
        response = c.get("/legislation/", {"q": "rabbits"})

        self.assertEqual(
            response.context["laws"][0].highlighted_sections()[0]["text"],
            "Brown <em>rabbits</em> are commonly seen.",
        )

    def test_classification_filtering(self):

        classification_ids = ["1", "97"]  # Arbitrary level 0 classifications

        c = Client()
        response = c.get("/legislation/", {"classifications[]": classification_ids})

        expected_law_classifications_set = {
            (1, 44, 97, 118),
            (1, 97, 118),
            (1, 44, 97, 118),
            (1, 118),
            (1, 44, 97, 118),
            (97,),
            (1, 118),
            (44, 97, 118),
        }
        # TODO: Intentionally define an order to be returned. Currently this
        # order is accidental, a result of ES's default scoring algorithms, so
        # we need to use sets instead of lists when testing.

        returned_law_classifications_set = {
            tuple(law.classifications.values_list("id", flat=True))
            for law in response.context["laws"]
        }

        self.assertEqual(
            expected_law_classifications_set, returned_law_classifications_set
        )

    def test_section_classification_filtering(self):

        classification_ids = ["3", "9"]  # Arbitrary non-0 level classifications

        laws = list(Legislation.objects.all())
        law1, law2 = laws[:2]  # Get two arbitrary laws

        section1 = law1.sections.create(
            text="Some text", legislation_page=1, code="Art. I"
        )

        section1.classifications.add(3)

        section2 = law2.sections.create(
            text="Some other text", legislation_page=1, code="Art. I"
        )

        section2.classifications.add(9)

        c = Client()
        response = c.get("/legislation/", {"classifications[]": classification_ids})

        expected_laws = [law1, law2]

        returned_laws = response.context["laws"].object_list

        self.assertEqual(expected_laws, returned_laws)

    def test_full_text_classification_search(self):

        q = "climate renewable"  # Arbitrary words found in classification names

        c = Client()
        response = c.get("/legislation/", {"q": q})

        returned_laws = response.context["laws"].object_list

        self.assertEqual(len(returned_laws), 6)
        self.assertIn(
            "Dedicated <em>climate</em> laws and governance",
            returned_laws[0].highlighted_classifications(),
        )

    def test_tag_filtering(self):

        tag_ids = ["1", "2"]  # Arbitrary tags

        c = Client()
        response = c.get("/legislation/", {"tags[]": tag_ids})

        expected_law_tag_set = {
            (4, (1,)),
            (8, (1, 2, 5, 6)),
            (6, (1, 2, 3, 4, 5, 6)),
            (10, (1, 2, 3, 4, 5, 6)),
            (5, (1, 2, 4, 5, 6)),
            (2, (2, 4)),
            (7, (1, 2, 3, 5, 6)),
            (1, (1, 2, 3, 4, 5, 6)),
            (3, (2, 3, 5)),
        }
        # TODO: Intentionally define an order to be returned. Currently this
        # order is accidental, a result of ES's default scoring algorithms, so
        # we need to use sets instead of lists when testing.

        returned_law_tag_set = {
            (law.id, tuple(law.tags.values_list("id", flat=True)))
            for law in response.context["laws"]
        }
        self.assertEqual(expected_law_tag_set, returned_law_tag_set)

    def test_section_tag_filtering(self):

        tag_ids = ["3", "4"]  # Arbitrary tags

        # Get two laws that are NOT tagged with those tags
        law1, law2 = Legislation.objects.filter(pk__in=[4, 8])

        # Add  sections to them and tag the sections with those tags
        section1 = law1.sections.create(
            text="Some text", legislation_page=1, code="Art. I"
        )

        section1.tags.add(3)

        section2 = law2.sections.create(
            text="Some other text", legislation_page=1, code="Art. I"
        )

        section2.tags.add(4)

        c = Client()
        response = c.get("/legislation/", {"tags[]": tag_ids})

        expected_law_tag_list = [
            (6, [1, 2, 3, 4, 5, 6]),
            (2, [2, 4]),
            (10, [1, 2, 3, 4, 5, 6]),
            (8, [1, 2, 5, 6]),  # Found inside section
            (4, [1]),  # Found inside section
            (1, [1, 2, 3, 4, 5, 6]),
            (9, [4]),
            (3, [2, 3, 5]),
            (5, [1, 2, 4, 5, 6]),
            (7, [1, 2, 3, 5, 6]),
        ]
        # NOTE: This list is ordered according to ElasticSearch default
        # algorithms. Currently this is considered good enough even though it
        # takes the length of tag names into account, which probably isn't
        # relevant in our case.

        returned_law_tag_list = [
            (law.id, list(law.tags.values_list("id", flat=True)))
            for law in response.context["laws"]
        ]
        self.assertEqual(expected_law_tag_list, returned_law_tag_list)

    def test_classification_and_tag_filtering(self):

        classification_id = 3  # Arbitrary non-top level classification
        tag_id = 1  # Arbitrary tag

        # Get two laws that are NOT tagged with this tag
        law1, law2 = Legislation.objects.exclude(tags__id=1)[:2]

        # Add an section to one of the legislations and classify it
        section1 = law1.sections.create(
            text="Some text", legislation_page=1, code="Art. I"
        )

        section1.classifications.add(classification_id)

        # Add an section to the other legislation and tag it
        section2 = law2.sections.create(
            text="Some other text", legislation_page=1, code="Art. I"
        )

        section2.tags.add(tag_id)

        c = Client()
        response = c.get(
            "/legislation/",
            {
                "partial": True,
                "classifications[]": [classification_id],
                "tags[]": [tag_id],
            },
        )
        self.assertEqual(len(response.context["laws"]), 0)

    def test_full_text_tag_search(self):

        q = "enforcement"  # Arbitrary word found in one of the tag names

        c = Client()
        response = c.get("/legislation/", {"q": q})

        returned_laws = response.context["laws"].object_list
        self.assertEqual(len(returned_laws), 7)
        self.assertIn(
            "Provisions for non-compliance and <em>enforcement</em>",
            returned_laws[0].highlighted_tags(),
        )

    def test_country_filtering(self):

        myanmar = "MMR"
        myanmar_class_id = 118

        c = Client()
        response = c.get("/legislation/", {"countries[]": myanmar})

        expected_law_ids = [4]
        myanmar_law = response.context["laws"][0]

        self.assertEqual(expected_law_ids, [myanmar_law.id])

        # Filter by country AND classification

        # Get a law that is NOT associated to Myanmar but has classification 93
        law = Legislation.objects.get(id=1)

        # Add a section to it
        law.sections.create(text="Some text", legislation_page=1, code="Art. I")

        response = c.get(
            "/legislation/",
            {
                "partial": True,
                "classifications[]": [myanmar_class_id],
                "countries[]": myanmar,
            },
        )

        expected_law_ids = [myanmar_law.id]
        # Only the Myanmar law is in the results
        returned_law_ids = [leg.id for leg in response.context["laws"]]
        self.assertEqual(expected_law_ids, returned_law_ids)

    def test_law_type_filtering(self):

        law_types = ["Law", "Constitution"]  # Arbitrary law types

        c = Client()
        response = c.get("/legislation/", {"law_types[]": law_types})

        expected_law_ids = [1, 2, 3, 5, 6, 10]
        returned_law_ids = [law.id for law in response.context["laws"]]

        self.assertEqual(expected_law_ids, returned_law_ids)

    def test_year_range_filtering(self):

        # Arbitrary years
        from_year = 1950
        to_year = 2005

        c = Client()
        response = c.get("/legislation/", {"from_year": from_year, "to_year": to_year})
        expected_law_ids = [3, 5, 6, 9, 10]
        returned_law_ids = [law.id for law in response.context["laws"]]

        self.assertEqual(expected_law_ids, returned_law_ids)

    @override_settings(LAWS_PER_PAGE=2)
    def test_pagination(self):

        c = Client()

        # Get all 10 legislations
        response = c.get("/legislation/")

        # Defaults to first page
        self.assertEqual(len(response.context["laws"]), 2)
        self.assertEqual(response.context["laws"].number, 1)

        # Get second page
        response = c.get("/legislation/", {"page": 2})

        # Returns second page
        self.assertEqual(len(response.context["laws"]), 2)
        self.assertEqual(response.context["laws"].number, 2)

        # Get 6 filtered legislations
        law_types = ["Law", "Constitution"]  # Law types that return 6 results
        response = c.get("/legislation/", {"law_types[]": law_types})

        # Defaults to first page
        self.assertEqual(len(response.context["laws"]), 2)
        self.assertEqual(response.context["laws"].number, 1)

        # Get second page
        response = c.get("/legislation/", {"law_types[]": law_types, "page": 2})
        self.assertEqual(len(response.context["laws"]), 2)
        self.assertEqual(response.context["laws"].number, 2)

        # Get 1 filtered legislation
        country_iso = "MMR"  # Country id that returns only one result
        response = c.get("/legislation/", {"countries[]": [country_iso]})

        self.assertEqual(len(response.context["laws"]), 1)
        self.assertEqual(response.context["laws"].number, 1)

        # Try to get second page (doesn't exist)
        response = c.get("/legislation/", {"countries[]": [country_iso], "page": 2})

        # Returns last existing page
        self.assertEqual(len(response.context["laws"]), 1)
        self.assertEqual(response.context["laws"].number, 1)

    def tearDown(self):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)


class LegislationExplorerOrder(TestCase):
    fixtures = [
        "Countries.json",
        "Gaps.json",
        "Questions.json",
        "TaxonomyClassification.json",
        "TaxonomyTag.json",
        "TaxonomyTagGroup.json",
        "LegislationForOrder.json",
    ]

    def setUp(self):
        with open(os.devnull, "w") as f:
            call_command("search_index", "--rebuild", "-f", stdout=f)

    @skip(
        "This test fails on travis, but works locally. It should be investigated more."
    )
    def test_phrase_match_prioritized(self):

        classifications = [1]
        law_types = ["Law"]

        c = Client()
        response = c.get(
            "/legislation/",
            {
                "q": "Exercise policy coordination",
                "classifications[]": classifications,
                "law_types[]": law_types,
            },
        )

        returned_law_ids = [law.id for law in response.context["laws"]]

        self.assertEqual(returned_law_ids[0], 69)

        # 69 is the id of the only one of the 3 laws in the database that
        # contains a section with the exact phrase
        # "Exercise policy coordination". It must appear at the top.
