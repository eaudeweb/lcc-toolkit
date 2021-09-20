from random import randint, shuffle

from django.core.management.base import BaseCommand

from lcc.models import TaxonomyClassification, TaxonomyTag
from lcc.factories import LegislationFactory


class Command(BaseCommand):

    help = "Generate fake legislation"

    def add_arguments(self, parser):
        parser.add_argument("num", type=int)

    def handle(self, *args, **options):

        # Legislation objects can only be tagged with level 0 classifications
        classifications = list(TaxonomyClassification.objects.filter(level=0))
        tags = list(TaxonomyTag.objects.all())

        for _ in range(options["num"]):

            num_class = randint(1, 4)
            num_tags = randint(1, 10)

            shuffle(classifications)
            shuffle(tags)

            law = LegislationFactory()
            law.save()
            law.classifications.add(*classifications[:num_class])
            law.tags.add(*tags[:num_tags])
