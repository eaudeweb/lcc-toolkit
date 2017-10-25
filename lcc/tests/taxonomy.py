from django_webtest import WebTest
from lcc.models import (
    TaxonomyTagGroup, TaxonomyTag, TaxonomyClassification
)


def create_taxonomy_tag_group(name="test_tag_group"):
    return TaxonomyTagGroup.objects.create(name=name)


def create_taxonomy_tag(group, name="test_tag"):
    return TaxonomyTag.objects.create(name=name, group=group)


def create_taxonomy_classication(name="test_classification", parent=None):
    return TaxonomyClassification.objects.create(name=name, parent=parent)


class TaxonomyTagGroupTest(WebTest):
    def test_tag_group_add(self):
        tag_group = create_taxonomy_tag_group()
        self.assertEqual(tag_group.name, "test_tag_group")
        second_tag_group = create_taxonomy_tag_group("test_another_tag_group")
        self.assertEqual(second_tag_group.name, "test_another_tag_group")


class TaxonomyTagTest(WebTest):
    def test_tag_add(self):
        tag_group = create_taxonomy_tag_group()
        second_tag_group = create_taxonomy_tag_group("test_another_tag_group")
        tag = create_taxonomy_tag(tag_group)
        self.assertEqual(tag.group, tag_group)
        self.assertEqual(tag_group.tags.count(), 1)
        self.assertEqual(second_tag_group.tags.count(), 0)


class TaxonomyClassificationTest(WebTest):
    def test_add_single_classification(self):
        classification = create_taxonomy_classication()
        self.assertEqual(classification.name, "test_classification")
        self.assertEqual(classification.code, "1")
        self.assertEqual(classification.parent, None)

    def test_add_multiple_classification(self):
        top_level = create_taxonomy_classication(name="top_level")
        second_level = create_taxonomy_classication(
            name="second_level", parent=top_level)
        third_level = create_taxonomy_classication(
            name="third_level", parent=second_level)

        # test parents
        self.assertEqual(second_level.parent, top_level)
        self.assertEqual(third_level.parent, second_level)

        # test codes
        self.assertEqual(top_level.code, "1")
        self.assertEqual(second_level.code, "1.1")
        self.assertEqual(third_level.code, "1.1.1")
