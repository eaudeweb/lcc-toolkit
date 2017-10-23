from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):

    help = "Load initial data"

    FIXTURES = ("TaxonomyTagGroup", "TaxonomyTag", "TaxonomyClassification",
                "Question", "Countries", "CountryMetadata")

    def handle(self, *args, **options):
        for fixture in Command.FIXTURES:
            call_command('loaddata', fixture)
