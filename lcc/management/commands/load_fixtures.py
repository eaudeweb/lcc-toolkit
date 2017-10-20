import lcc.constants as lcc_constants
import lcc.models as lcc_models

from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):

    help = "Load initial data"

    FIXTURES = ("TaxonomyTagGroup", "TaxonomyTag", "TaxonomyClassification",
                "Question", "Countries", "Legislation")

    def handle(self, *args, **options):
        for fixture in Command.FIXTURES:
            call_command('loaddata', fixture)
