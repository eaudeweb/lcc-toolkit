from django.test import Client, TestCase
from django.urls import reverse


class InformationPagesTest(TestCase):
    fixtures = [
        'Countries.json',
        'Gaps.json',
        'Questions.json',
        'TaxonomyClassification.json',
        'TaxonomyTag.json',
        'TaxonomyTagGroup.json',
        'Legislation.json',
    ]

    def test_homepage(self):
        c = Client()
        response = c.get(reverse('lcc:home_page'))
        self.assertEqual(response.status_code, 200)
    
    def test_about_page(self):
        c = Client()
        response = c.get(reverse('lcc:about_us'))
        self.assertEqual(response.status_code, 200)
