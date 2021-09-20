import json

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from lcc.models import Answer, Assessment, Country, Question
from lcc.serializers import AnswerSerializer
from lcc.tests.taxonomy import create_taxonomy_classication


class GetAnswersTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("testuser", "user@test.com", "test1234")
        self.client.login(username="testuser", password="test1234")
        self.country = Country.objects.create(iso="ROU", name="Romania")
        self.assessment = Assessment.objects.create(
            user=self.user, country=self.country
        )
        self.classification = create_taxonomy_classication()

        self.question_1 = Question.objects.create(
            text="Question 1 text",
            parent=None,
            order=1,
            classification=self.classification,
        )
        self.question_2 = Question.objects.create(
            text="Question 2 text",
            parent=None,
            order=2,
            classification=self.classification,
        )
        self.question_3 = Question.objects.create(
            text="Question 3 text",
            parent=self.question_1,
            order=1,
            classification=self.classification,
        )
        self.question_4 = Question.objects.create(
            text="Question 4 text",
            parent=self.question_2,
            order=1,
            classification=self.classification,
        )

        self.answer_1 = Answer.objects.create(
            assessment=self.assessment, question=self.question_1, value=True
        )
        self.answer_2 = Answer.objects.create(
            assessment=self.assessment, question=self.question_2, value=True
        )
        self.answer_3 = Answer.objects.create(
            assessment=self.assessment, question=self.question_3, value=False
        )

    def test_get_all_answers(self):
        response = self.client.get(reverse("lcc:api:answers_list_create"))
        answers = Answer.objects.all()
        serializer = AnswerSerializer(answers, many=True)
        json_res = json.loads(response.content.decode())
        json_ser = json.loads(json.dumps(serializer.data))
        self.assertEqual(json_res, json_ser)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_single_answer(self):
        response = self.client.get(
            reverse("lcc:api:answers_get_update", args=[self.answer_1.pk])
        )
        serializer = AnswerSerializer(self.answer_1)
        json_res = json.loads(response.content.decode())
        json_ser = json.loads(json.dumps(serializer.data))
        self.assertEqual(json_res, json_ser)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_invalid_single_answer(self):
        response = self.client.get(
            reverse("lcc:api:answers_get_update", args=[100]), expect_errors=True
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CreateAnswersTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("testuser", "user@test.com", "test1234")
        self.client.login(username="testuser", password="test1234")
        self.country = Country.objects.create(iso="ro", name="Romania")
        self.assessment = Assessment.objects.create(
            user=self.user, country=self.country
        )
        self.classification = create_taxonomy_classication()

        self.question_1 = Question.objects.create(
            text="Question 1 text",
            parent=None,
            order=1,
            classification=self.classification,
        )

        self.answer_valid_payload = {
            "assessment": self.assessment.pk,
            "question": self.question_1.pk,
            "value": True,
        }

        self.answer_invalid_payload = {
            "assessment": self.assessment.pk,
            "question": self.question_1.pk,
            "value": None,
        }

    def test_create_valid_answer(self):
        response = self.client.post(
            reverse("lcc:api:answers_list_create"),
            json.dumps(self.answer_valid_payload),
            data_type="json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_invalid_answer(self):
        response = self.client.post(
            reverse("lcc:api:answers_list_create"),
            json.dumps(self.answer_invalid_payload),
            data_type="json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UpdateSingleAnswer(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("testuser", "user@test.com", "test1234")
        self.client.login(username="testuser", password="test1234")
        self.country = Country.objects.create(iso="ROU", name="Romania")
        self.assessment = Assessment.objects.create(
            user=self.user, country=self.country
        )
        self.classification = create_taxonomy_classication()

        self.question_1 = Question.objects.create(
            text="Question 1 text",
            parent=None,
            order=1,
            classification=self.classification,
        )

        self.answer_1 = Answer.objects.create(
            assessment=self.assessment, question=self.question_1, value=True
        )

        self.answer_valid_payload = {
            "assessment": self.assessment.pk,
            "question": self.question_1.pk,
            "value": not self.answer_1.value,
        }

        self.answer_invalid_payload = {
            "assessment": self.assessment.pk,
            "question": self.question_1.pk,
            "value": None,
        }

    def test_valid_update_answer(self):
        response = self.client.put(
            reverse("lcc:api:answers_get_update", args=[self.answer_1.pk]),
            json.dumps(
                {
                    "assessment": self.assessment.pk,
                    "question": self.question_1.pk,
                    "value": False,
                }
            ),
            data_type="json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
