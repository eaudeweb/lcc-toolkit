from django.test import Client, TestCase
from django.urls import reverse

from lcc.models import Question


class QuestionTests(TestCase):
    fixtures = [
        "Countries.json",
        "Gaps.json",
        "Questions.json",
        "TaxonomyClassification.json",
        "TaxonomyTag.json",
        "TaxonomyTagGroup.json",
        "Legislation.json",
    ]

    def test_question_list_view(self):
        c = Client()
        response = c.get(
            reverse("lcc:api:question_category", kwargs={"category_pk": 1})
        )
        self.assertEqual(response.status_code, 200)
