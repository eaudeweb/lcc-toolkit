from django.core.management.base import BaseCommand
from lcc.models import TaxonomyTag, TaxonomyClassification


class Command(BaseCommand):

    help = "Load initial data"

    def handle(self, *args, **options):
        for tax_cls in TaxonomyClassification.objects.all():
            count = tax_cls.code.count('.')
            if count == 0:
                print('{0} - pk {1} - {2}\n'.format(
                    tax_cls.code, tax_cls.pk, tax_cls.name
                ))

            if count == 1:
                print('\t{0} - pk {1} - {2}\n'.format(
                    tax_cls.code, tax_cls.pk, tax_cls.name
                ))

            if count == 2:
                print('\t\t{0} - pk {1} - {2}\n'.format(
                    tax_cls.code, tax_cls.pk, tax_cls.name
                ))

        print("End class")

        for tag in TaxonomyTag.objects.all():
            print('{0} - {1}\n'.format(tag.pk, tag.name))

        print("End tag")
