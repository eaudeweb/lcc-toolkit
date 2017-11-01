from django.core.management.base import BaseCommand
from django.core.management import call_command
from lcc.models import (
    TaxonomyTagGroup, TaxonomyTag, TaxonomyClassification,
    Gap, Question
)


class Command(BaseCommand):

    help = "Load initial data"

    FIXTURES = ("TaxonomyTagGroup", "TaxonomyTag", "TaxonomyClassification",
                "Countries", "CountryMetadata", "Gaps", "Questions")

    def handle(self, *args, **options):
        TaxonomyTagGroup.objects.all().delete()
        TaxonomyTag.objects.all().delete()
        TaxonomyClassification.objects.all().delete()
        Gap.objects.all().delete()
        Question.objects.all().delete()
        for fixture in Command.FIXTURES:
            call_command('loaddata', fixture)
