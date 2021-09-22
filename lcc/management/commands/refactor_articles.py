from django.core.management.base import BaseCommand
from lcc.models import (
    Legislation, LegislationArticle, LegislationSection
)
import re

# 22, 5, 52, 44

# Legislation 78 has a tree articles structure, but it does not follow a pattern. Thus,
# the legislation's articles will be translated into flat sections

class Command(BaseCommand):

    help = "Refactor articles into tree sections"

    def handle(self, *args, **options):
        # LegislationSection.objects.all().delete()
        single_leaf_leg =  Legislation.objects.filter(
            import_from_legispro=False
        ).exclude(
            pk__in=[5, 22, 44, 52]
        )
        for leg in single_leaf_leg:
            print("Processing legislation {}".format(leg.title))
            for idx, article in enumerate(leg.articles.all(), start=1):
                new_article = LegislationSection.objects.create(
                    text=article.text,
                    legislation=article.legislation,
                    legislation_page=article.legislation_page,
                    code=article.code,
                    code_order= idx,
                    number=article.number,
                    identifier=article.identifier,
                    legispro_identifier=article.legispro_identifier,
                    parent=None,
                )
                new_article.classifications.set(article.classifications.all())
                new_article.tags.set(article.tags.all())
                new_article.save()
                print("Created new section {}".format(new_article.code))

        tree_articles_letters = Legislation.objects.filter(pk__in=[5, 44])
        tree_article_dashes = Legislation.objects.filter(pk__in=[22, 52])

        for leg in tree_article_dashes:
            print("Processing legislation {}".format(leg.title))
            previous = None
            parent = None
            code_order = 1
            for article in leg.articles.all():
                if previous and previous.number == article.number:
                    if not parent:
                        parent = previous
                else:
                    code_order += 1
                    parent = None

                y = re.search("^[Article ]+\d+-", article.code)
                if y:
                    if parent:
                        article_tree = LegislationSection.objects.create(
                            text=article.text,
                            legislation=article.legislation,
                            legislation_page=article.legislation_page,
                            code=article.code,
                            code_order="{}.{}".format(parent.code_order,parent.get_children().count() + 1),
                            number=article.number,
                            identifier=article.identifier,
                            legispro_identifier=article.legispro_identifier,
                            parent=parent,
                        )
                        print("Created new section {}, code order: {}".format(article_tree.code, article_tree.code_order))

                else:
                    article_tree = LegislationSection.objects.create(
                        text=article.text,
                        legislation=article.legislation,
                        legislation_page=article.legislation_page,
                        code=article.code,
                        code_order=code_order,
                        number=article.number,
                        identifier=article.identifier,
                        legispro_identifier=article.legispro_identifier,
                        parent=None,
                    )
                    print("Created new section {}, coder order: {}".format(article_tree.code, article_tree.code_order))
                    # parent = None
                
                article_tree.classifications.set(article.classifications.all())
                article_tree.tags.set(article.tags.all())
                article_tree.save()
                previous = article_tree

        for leg in tree_articles_letters:
            print("Processing legislation {}".format(leg.title))
            previous = None
            parent = None
            parent_2 = None
            code_order = 1
            for article in leg.articles.all():
                if previous and previous.number == article.number:
                    if not parent:
                        parent = previous
                else:
                    code_order += 1
                    parent = None

                y = re.search("^\d+[A-Z]{2}", article.code)
                x = re.search("^\d+[A-Z]", article.code)
                if y:
                    if not parent_2:
                        parent_2 = previous
                    article_tree = LegislationSection.objects.create(
                        text=article.text,
                        legislation=article.legislation,
                        legislation_page=article.legislation_page,
                        code=article.code,
                        code_order="{}.{}".format(parent_2.code_order,parent_2.get_children().count() + 1),
                        number=article.number,
                        identifier=article.identifier,
                        legispro_identifier=article.legispro_identifier,
                        parent=parent_2,
                    )
                    print("Created new section {}, code order: {}".format(article_tree.code, article_tree.code_order))
                elif x:
                    article_tree = LegislationSection.objects.create(
                        text=article.text,
                        legislation=article.legislation,
                        legislation_page=article.legislation_page,
                        code=article.code,
                        code_order="{}.{}".format(parent.code_order,parent.get_children().count() + 1),
                        number=article.number,
                        identifier=article.identifier,
                        legispro_identifier=article.legispro_identifier,
                        parent=parent,
                    )
                    print("Created new section {}, coder order: {}".format(article_tree.code, article_tree.code_order))
                    parent_2 = None
                else:
                    if not parent:
                        order = code_order
                    else:
                        order = "{}.{}".format(parent.code_order,parent.get_children().count() + 1)
                    article_tree = LegislationSection.objects.create(
                        text=article.text,
                        legislation=article.legislation,
                        legislation_page=article.legislation_page,
                        code=article.code,
                        code_order=order,
                        number=article.number,
                        identifier=article.identifier,
                        legispro_identifier=article.legispro_identifier,
                        parent=parent,
                    )
                    print("Created new section {}, code order: {}".format(article_tree.code, article_tree.code_order))
                    parent = None
                    parent_2 = None
                
                article_tree.classifications.set(article.classifications.all())
                article_tree.tags.set(article.tags.all())
                article_tree.save()
                previous = article_tree

        # for leg in tree_articles_letters:
        #     for atree in leg.articles.all():
        #         if atree.parent:
        #             dashes = "----" * atree.level
        #             print(f"{dashes}{atree.code} (((parent: {atree.parent.code})))")
        #         else:
        #             print(atree.code)
