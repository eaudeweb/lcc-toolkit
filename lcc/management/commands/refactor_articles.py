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
        single_leaf_leg =  Legislation.objects.filter(
            import_from_legispro=False
        ).exclude(
            pk__in=[5, 22, 44, 52]
        )
        for leg in single_leaf_leg:
            print("Processing legislation {}".format(leg.title))
            for article in leg.articles.all():
                new_article = LegislationSection.objects.create(
                    text=article.text,
                    legislation=article.legislation,
                    legislation_page=article.legislation_page,
                    code=article.code,
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
            for article in leg.articles.all():
                if previous and previous.number == article.number:
                    if not parent:
                        parent = previous
                else:
                    parent = None

                y = re.search("^[Article ]+\d+-", article.code)
                if y:
                    if parent:
                        article_tree = LegislationSection.objects.create(
                            text=article.text,
                            legislation=article.legislation,
                            legislation_page=article.legislation_page,
                            code=article.code,
                            number=article.number,
                            identifier=article.identifier,
                            legispro_identifier=article.legispro_identifier,
                            parent=parent,
                        )
                        print("Created new section {}".format(new_article.code))

                else:
                    article_tree = LegislationSection.objects.create(
                        text=article.text,
                        legislation=article.legislation,
                        legislation_page=article.legislation_page,
                        code=article.code,
                        number=article.number,
                        identifier=article.identifier,
                        legispro_identifier=article.legispro_identifier,
                        parent=None,
                    )
                    print("Created new section {}".format(new_article.code))
                    parent = None
                
                article_tree.classifications.set(article.classifications.all())
                article_tree.tags.set(article.tags.all())
                article_tree.save()
                previous = article_tree

        for leg in tree_articles_letters:
            print("Processing legislation {}".format(leg.title))
            previous = None
            parent = None
            parent_2 = None
            for article in leg.articles.all():
                if previous and previous.number == article.number:
                    if not parent:
                        parent = previous
                else:
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
                        number=article.number,
                        identifier=article.identifier,
                        legispro_identifier=article.legispro_identifier,
                        parent=parent_2,
                    )
                    print("Created new section {}".format(new_article.code))
                elif x:
                    article_tree = LegislationSection.objects.create(
                        text=article.text,
                        legislation=article.legislation,
                        legislation_page=article.legislation_page,
                        code=article.code,
                        number=article.number,
                        identifier=article.identifier,
                        legispro_identifier=article.legispro_identifier,
                        parent=parent,
                    )
                    print("Created new section {}".format(new_article.code))
                    parent_2 = None
                else:
                    article_tree = LegislationSection.objects.create(
                        text=article.text,
                        legislation=article.legislation,
                        legislation_page=article.legislation_page,
                        code=article.code,
                        number=article.number,
                        identifier=article.identifier,
                        legispro_identifier=article.legispro_identifier,
                        parent=parent,
                    )
                    print("Created new section {}".format(new_article.code))
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
