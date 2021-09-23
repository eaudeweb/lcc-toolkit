from django.core.management.base import BaseCommand
from lcc.models import (
    Legislation, LegislationSection
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
            pk__in=[5, 22, 44, 52, 63]
        )
        with LegislationSection.objects.disable_mptt_updates():
            print("Start single leaf\n\n\n")
            for leg in single_leaf_leg:
                print("Processing legislation {}".format(leg.title))
                for idx, article in enumerate(leg.articles.all(), start=1):
                    section = LegislationSection.objects.create(
                        text=article.text,
                        legislation=article.legislation,
                        legislation_page=article.legislation_page,
                        code=article.code,
                        code_order=idx,
                        number=article.number,
                        identifier=article.identifier,
                        legispro_identifier=article.legispro_identifier,
                        parent=None,
                    )
                    section.classifications.set(article.classifications.all())
                    section.tags.set(article.tags.all())
                    section.save()
                    print("Created new section {}".format(section.code))

            tree_articles_letters = Legislation.objects.filter(pk__in=[5, 44, 63])
            tree_article_dashes = Legislation.objects.filter(pk__in=[22, 52])

            print("Start dashes\n\n\n")
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
                            section = LegislationSection.objects.create(
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
                            print("Created new section {}, code order: {}".format(section.code, section.code_order))
                    else:
                        section = LegislationSection.objects.create(
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
                        print("Created new section {}, coder order: {}".format(section.code, section.code_order))
                        parent = None
                        
                        section.classifications.set(article.classifications.all())
                        section.tags.set(article.tags.all())
                        section.save()
                        previous = section

            print("Start letters\n\n")
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
                        section = LegislationSection.objects.create(
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
                        print("Created new section {}, code order: {}".format(section.code, section.code_order))
                    elif x:
                        if not parent:
                            order = code_order
                        else:
                            order = "{}.{}".format(parent.code_order,parent.get_children().count() + 1)
                        section = LegislationSection.objects.create(
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
                        print("Created new section {}, coder order: {}".format(section.code, section.code_order))
                        parent_2 = None
                    else:
                        if not parent:
                            order = code_order
                        else:
                            order = "{}.{}".format(parent.code_order,parent.get_children().count() + 1)
                        section = LegislationSection.objects.create(
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
                        print("Created new section {}, code order: {}".format(section.code, section.code_order))
                        parent = None
                        parent_2 = None
                    
                    section.classifications.set(article.classifications.all())
                    section.tags.set(article.tags.all())
                    section.save()
                    previous = section

        LegislationSection.objects.rebuild()
        # for leg in tree_articles_letters:
        #     for atree in leg.sections.all():
        #         if atree.parent:
        #             dashes = "----" * atree.level
        #             print(f"{dashes}{atree.code} (((parent: {atree.parent.code})))")
        #         else:
        #             print(atree.code)
