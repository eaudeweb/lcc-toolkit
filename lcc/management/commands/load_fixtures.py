from django.core.management.base import BaseCommand
from django.core.management import call_command
from lcc.models import (
    TaxonomyTagGroup, TaxonomyTag, TaxonomyClassification,
    Gap, Question
)


class Command(BaseCommand):

    help = "Load initial data"

    FIXTURES = ("TaxonomyTagGroup", "TaxonomyTag", "TaxonomyClassification",
                "Countries", "Questions", "Gaps")

    def handle(self, *args, **options):
        for fixture in Command.FIXTURES:
            call_command('loaddata', fixture)
