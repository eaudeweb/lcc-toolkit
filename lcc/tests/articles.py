import os

from django.contrib.auth.models import User, Group
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from lcc.models import Legislation, LegislationArticle, UserProfile


class Articles(TestCase):
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

        content_manager_group = Group.objects.get(name='Content manager')
        policy_maker_group = Group.objects.get(name='Policy maker')

        content_manager = User.objects.create(username='manager')
        content_manager.set_password('foobar')
        content_manager.save()
        UserProfile.objects.create(user=content_manager, home_country_id='AFG')

        content_manager.groups.add(content_manager_group)

        policy_maker = User.objects.create(username='policymaker')
        policy_maker.set_password('foobar')
        policy_maker.save()
        UserProfile.objects.create(user=policy_maker, home_country_id='AFG')

        policy_maker.groups.add(policy_maker_group)

        self.law = Legislation.objects.first()
        self.article_data = {
            "text": "Brown rabbits are commonly seen.",
            "legislation_page": 1,
            "legislation": self.law.id,
            "code": "Art. I",
        }
        self.article = self.law.articles.create(**self.article_data)

        with open(os.devnull, 'w') as f:
            call_command('search_index', '--rebuild', '-f', stdout=f)

    def test_needs_perm_to_add_articles(self):

        c = Client()
        c.login(username='policymaker', password='foobar')
        response = c.get('/legislation/{}/articles/add/'.format(self.law.id))

        self.assertEqual(response.status_code, 302)  # Temporary redirect

        c.login(username='manager', password='foobar')
        response = c.get('/legislation/{}/articles/add/'.format(self.law.id))

        self.assertEqual(response.status_code, 200)  # OK

    def test_needs_perm_to_edit_articles(self):

        c = Client()
        c.login(username='policymaker', password='foobar')
        response = c.get(
            '/legislation/{}/articles/{}/edit/'.format(
                self.law.id, self.article.id)
        )

        self.assertEqual(response.status_code, 302)  # Temporary redirect

        c.login(username='manager', password='foobar')
        response = c.get(
            '/legislation/{}/articles/{}/edit/'.format(
                self.law.id, self.article.id)
        )

        self.assertEqual(response.status_code, 200)  # OK

    def test_needs_perm_to_delete_articles(self):

        c = Client()
        c.login(username='policymaker', password='foobar')
        response = c.get(
            '/legislation/{}/articles/{}/delete/'.format(
                self.law.id, self.article.id)
        )

        self.assertEqual(response.status_code, 302)  # Temporary redirect

        c.login(username='manager', password='foobar')
        self.assertEqual(self.law.articles.count(), 1)
        response = c.get(
            '/legislation/{}/articles/{}/delete/'.format(
                self.law.id, self.article.id)
        )
        self.assertEqual(response.status_code, 302)  # Temporary redirect
        self.assertEqual(self.law.articles.count(), 0)

    def test_needs_perm_to_see_add_articles_link(self):

        c = Client()
        c.login(username='policymaker', password='foobar')
        response = c.get('/legislation/{}/'.format(self.law.id))

        self.assertNotContains(
            response,
            'href="/legislation/{}/articles/add/"'.format(self.law.id)
        )

        c.login(username='manager', password='foobar')
        response = c.get('/legislation/{}/articles/add/'.format(self.law.id))

        self.assertContains(
            response,
            'href="/legislation/{}/articles/add/"'.format(self.law.id)
        )

    def test_needs_perm_to_see_edit_articles_link(self):

        c = Client()
        c.login(username='policymaker', password='foobar')
        response = c.get('/legislation/{}/articles/'.format(self.law.id))

        self.assertNotContains(
            response,
            'href="/legislation/{}/articles/{}/edit/"'.format(
                self.law.id, self.article.id)
        )

        c.login(username='manager', password='foobar')
        response = c.get('/legislation/{}/articles/'.format(self.law.id))

        self.assertContains(
            response,
            'href="/legislation/{}/articles/{}/edit/"'.format(
                self.law.id, self.article.id)
        )

    def test_needs_perm_to_see_delete_articles_link(self):

        c = Client()
        c.login(username='policymaker', password='foobar')
        response = c.get('/legislation/{}/articles/'.format(self.law.id))

        self.assertNotContains(
            response,
            'href="/legislation/{}/articles/{}/delete/"'.format(
                self.law.id, self.article.id)
        )

        c.login(username='manager', password='foobar')
        response = c.get('/legislation/{}/articles/'.format(self.law.id))

        self.assertContains(
            response,
            'href="/legislation/{}/articles/{}/delete/"'.format(
                self.law.id, self.article.id)
        )

    def test_article_order(self):
        law = Legislation.objects.last()
        for number in [3, 1, 2]:  # Not in order
            law.articles.create(
                text="Brown rabbits are commonly seen.",
                legislation_page=number,  # Any value, doesn't matter
                code="Art. {} of the law".format(number)
            )
        # In order
        self.assertEqual(
            list(law.articles.values_list('number', flat=True)), [1, 2, 3])

    def test_article_number_updated(self):
        law = Legislation.objects.last()
        for number in [3, 1, 5]:  # Not in order
            law.articles.create(
                text="Brown rabbits are commonly seen.",
                legislation_page=number,  # Any value, doesn't matter
                code="Art. {} of the law".format(number)
            )

        article = law.articles.get(number=5)
        article.code = "Art. 2 of the law"
        article.save()

        self.assertEqual(article.number, 2)

    def test_article_create(self):
        law = Legislation.objects.last()
        article_data = {
            "text": "Brown rabbits are commonly seen.",
            "legislation_page": 3,
            "legislation": law.id,
            "code": "Art. 3 of the law",
        }
        article_data.update({"save-btn": ""})
        c = Client()
        c.login(username='manager', password='foobar')
        response = c.post(
            reverse("lcc:legislation:articles:add",
            kwargs={"legislation_pk": law.id}),
            data=article_data
        )
        article = LegislationArticle.objects.first()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("lcc:legislation:articles:view",
            kwargs={"legislation_pk": law.id})
        )
        self.assertEqual(article.text, article_data['text'])
        self.assertEqual(article.legislation.id, article_data['legislation'])
        self.assertEqual(article.legislation_page, article_data['legislation_page'])
        self.assertEqual(article.code, article_data['code'])

    def test_article_create_and_continue(self):
        self.article_data.update({"save-and-continue-btn": ""})
        c = Client()
        c.login(username='manager', password='foobar')
        response = c.post(
            reverse("lcc:legislation:articles:add",
            kwargs={"legislation_pk": self.law.id}),
            data=self.article_data
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("lcc:legislation:articles:add",
            kwargs={"legislation_pk": self.law.id})
        )

    def test_edit_article(self):
        c = Client()
        c.login(username='manager', password='foobar')
        self.article_data['code'] = "{}"
        self.article_data['text'] = "text updated"
        response = c.post(
            reverse("lcc:legislation:articles:edit",
            kwargs={"legislation_pk": self.article.legislation.id,
                    "article_pk": self.article.id}),
            data=self.article_data
        )
        self.assertEqual(response.status_code, 302)
        article = LegislationArticle.objects.first()
        self.assertEqual(article.text, self.article_data['text'])

    def test_edit_article_fail_form(self):
        c = Client()
        c.login(username='manager', password='foobar')
        response = c.post(
            reverse("lcc:legislation:articles:edit",
            kwargs={"legislation_pk": self.law.id,
                    "article_pk": self.article.id}),
            data={"text": 234}
        )
        self.assertEqual(response.status_code, 302)
