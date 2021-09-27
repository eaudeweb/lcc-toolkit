import os

from django.contrib.auth.models import User, Group
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from lcc.models import Legislation, LegislationSection, UserProfile


class Sections(TestCase):
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

        content_manager_group = Group.objects.get(name="Content manager")
        policy_maker_group = Group.objects.get(name="Policy maker")

        content_manager = User.objects.create(username="manager")
        content_manager.set_password("foobar")
        content_manager.save()
        UserProfile.objects.create(user=content_manager, home_country_id="AFG")

        content_manager.groups.add(content_manager_group)

        policy_maker = User.objects.create(username="policymaker")
        policy_maker.set_password("foobar")
        policy_maker.save()
        UserProfile.objects.create(user=policy_maker, home_country_id="AFG")

        policy_maker.groups.add(policy_maker_group)

        self.law = Legislation.objects.first()
        self.law.pdf_file = SimpleUploadedFile(
            "Legislation_3_-_ccra2002212.pdf", b"these are the file contents!"
        )
        self.law.save()
        self.section_data = {
            "text": "Brown rabbits are commonly seen.",
            "legislation_page": 1,
            "legislation": self.law.id,
            "code": "Art. I",
            "code_order": "1",
        }
        self.section = self.law.sections.create(**self.section_data)

        with open(os.devnull, "w") as f:
            call_command("search_index", "--rebuild", "-f", stdout=f)

    def test_needs_perm_to_add_sections(self):

        c = Client()
        c.login(username="policymaker", password="foobar")
        url = reverse(
            "lcc:legislation:sections:add", kwargs={"legislation_pk": self.law.id}
        )
        response = c.get(url)
        self.assertEqual(response.status_code, 302)  # Temporary redirect

        c.login(username="manager", password="foobar")
        response = c.get(url)

        self.assertEqual(response.status_code, 200)  # OK

    def test_needs_perm_to_edit_sections(self):

        c = Client()
        c.login(username="policymaker", password="foobar")
        url = reverse(
            "lcc:legislation:sections:edit",
            kwargs={"legislation_pk": self.law.id, "section_pk": self.section.id},
        )
        response = c.get(url)

        self.assertEqual(response.status_code, 302)  # Temporary redirect

        c.login(username="manager", password="foobar")
        response = c.get(url)

        self.assertEqual(response.status_code, 200)  # OK

    def test_needs_perm_to_delete_sections(self):

        c = Client()
        c.login(username="policymaker", password="foobar")
        url = reverse(
            "lcc:legislation:sections:delete",
            kwargs={"legislation_pk": self.law.id, "section_pk": self.section.id},
        )
        response = c.get(url)

        self.assertEqual(response.status_code, 302)  # Temporary redirect

        c.login(username="manager", password="foobar")
        self.assertEqual(self.law.sections.count(), 1)
        response = c.get(url)
        self.assertEqual(response.status_code, 302)  # Temporary redirect
        self.assertEqual(self.law.sections.count(), 0)

    def test_needs_perm_to_see_add_sections_link(self):

        c = Client()
        c.login(username="policymaker", password="foobar")
        response = c.get("/legislation/{}/".format(self.law.id))

        self.assertNotContains(
            response,
            'href="{}"'.format(
                reverse(
                    "lcc:legislation:sections:add",
                    kwargs={"legislation_pk": self.law.id},
                )
            ),
        )

        c.login(username="manager", password="foobar")
        response = c.get(
            reverse(
                "lcc:legislation:sections:add", kwargs={"legislation_pk": self.law.id}
            )
        )

        self.assertContains(
            response,
            'href="{}"'.format(
                reverse(
                    "lcc:legislation:sections:add",
                    kwargs={"legislation_pk": self.law.id},
                )
            ),
        )

    def test_needs_perm_to_see_edit_sections_link(self):

        c = Client()
        c.login(username="policymaker", password="foobar")
        response = c.get(
            reverse(
                "lcc:legislation:sections:view", kwargs={"legislation_pk": self.law.id}
            )
        )

        url = reverse(
            "lcc:legislation:sections:edit",
            kwargs={"legislation_pk": self.law.id, "section_pk": self.section.id},
        )

        self.assertNotContains(response, 'href="{}"'.format(url))

        c.login(username="manager", password="foobar")
        response = c.get(
            reverse(
                "lcc:legislation:sections:view", kwargs={"legislation_pk": self.law.id}
            )
        )

        self.assertContains(response, 'href="{}"'.format(url))

    def test_needs_perm_to_see_delete_sections_link(self):

        c = Client()
        c.login(username="policymaker", password="foobar")
        response = c.get(
            reverse(
                "lcc:legislation:sections:view", kwargs={"legislation_pk": self.law.id}
            )
        )

        url = reverse(
            "lcc:legislation:sections:delete",
            kwargs={"legislation_pk": self.law.id, "section_pk": self.section.id},
        )

        self.assertNotContains(response, 'href="{}"'.format(url))

        c.login(username="manager", password="foobar")
        response = c.get(
            reverse(
                "lcc:legislation:sections:view", kwargs={"legislation_pk": self.law.id}
            )
        )

        self.assertContains(response, 'href="{}"'.format(url))

    def test_section_order(self):
        law = Legislation.objects.last()
        for number in [3, 1, 2]:  # Not in order
            law.sections.create(
                text="Brown rabbits are commonly seen.",
                legislation_page=number,  # Any value, doesn't matter
                code="Art. {} of the law".format(number),
            )
        # In order
        self.assertEqual(list(law.sections.values_list("number", flat=True)), [1, 2, 3])

    def test_section_number_updated(self):
        law = Legislation.objects.last()
        for number in [3, 1, 5]:  # Not in order
            law.sections.create(
                text="Brown rabbits are commonly seen.",
                legislation_page=number,  # Any value, doesn't matter
                code="Art. {} of the law".format(number),
            )

        section = law.sections.get(number=5)
        section.code = "Art. 2 of the law"
        section.save()

        self.assertEqual(section.number, 2)

    def test_section_create(self):
        law = Legislation.objects.last()
        section_data = {
            "text": "Brown rabbits are commonly seen.",
            "legislation_page": 3,
            "parent": self.section.id,
            "legislation": law.id,
            "code": "Art. 3 of the law",
        }
        section_data.update({"save-btn": ""})
        c = Client()
        c.login(username="manager", password="foobar")
        response = c.post(
            reverse("lcc:legislation:sections:add", kwargs={"legislation_pk": law.id}),
            data=section_data,
        )
        section = LegislationSection.objects.first()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("lcc:legislation:sections:view", kwargs={"legislation_pk": law.id}),
        )
        self.assertEqual(section.text, section_data["text"])
        self.assertEqual(section.legislation.id, section_data["legislation"])
        self.assertEqual(section.parent.id, section_data["parent"])
        self.assertEqual(section.legislation_page, section_data["legislation_page"])
        self.assertEqual(section.code, section_data["code"])
        self.assertEqual(section.code_order, "1.1")

    def test_section_create_and_continue(self):
        self.section_data.update({"save-and-continue-btn": ""})
        c = Client()
        c.login(username="manager", password="foobar")
        response = c.post(
            reverse(
                "lcc:legislation:sections:add", kwargs={"legislation_pk": self.law.id}
            ),
            data=self.section_data,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse(
                "lcc:legislation:sections:add", kwargs={"legislation_pk": self.law.id}
            ),
        )

    def test_edit_section(self):
        c = Client()
        c.login(username="manager", password="foobar")
        self.section_data["code"] = "{}"
        self.section_data["text"] = "text updated"
        self.section_data["code_order"] = "1.1"
        self.section_data["parent"] = self.section
        new_section = self.law.sections.create(**self.section_data)
        response = c.post(
            reverse(
                "lcc:legislation:sections:edit",
                kwargs={
                    "legislation_pk": new_section.legislation.id,
                    "section_pk": new_section.id,
                },
            ),
            data=self.section_data,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(new_section.text, self.section_data["text"])
        self.assertEqual(new_section.parent, self.section_data["parent"])

    def test_edit_section_fail_form(self):
        c = Client()
        c.login(username="manager", password="foobar")
        response = c.post(
            reverse(
                "lcc:legislation:sections:edit",
                kwargs={"legislation_pk": self.law.id, "section_pk": self.section.id},
            ),
            data={"text": 234},
        )
        self.assertEqual(response.status_code, 302)
