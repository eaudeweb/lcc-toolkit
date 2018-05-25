import os

from django.contrib.auth.models import User, Group
from django.core.management import call_command
from django.test import Client, TestCase

from lcc.models import Legislation, UserProfile


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
        self.article = self.law.articles.create(
            text="Brown rabbits are commonly seen.",
            legislation_page=1,
            code="Art. I"
        )

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
