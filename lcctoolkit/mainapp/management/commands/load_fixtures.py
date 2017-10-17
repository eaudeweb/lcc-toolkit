import lcctoolkit.mainapp.constants as mainapp_constants
import lcctoolkit.mainapp.models as mainapp_models

from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):

    help = "Load initial data"

    FIXTURES = ("TaxonomyTagGroup", "TaxonomyTag",
                "TaxonomyClassification", "Countries", "Legislation")

    def handle(self, *args, **options):
        for fixture in Command.FIXTURES:
            call_command('loaddata', fixture)
