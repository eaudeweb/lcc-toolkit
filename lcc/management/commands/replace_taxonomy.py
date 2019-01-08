from django.core.management import call_command
from django.core.management.base import BaseCommand

from lcc.models import (
    TaxonomyClassification,
    Question,
    Gap,
)


class Command(BaseCommand):

    help = "Safely replace current Taxonomy and related Questions and Gaps."

    FIXTURES = ("TaxonomyClassification", "Questions", "Gaps")

    def handle(self, *args, **options):
        TaxonomyClassification.objects.all().delete()
        Question.objects.all().delete()
        Gap.objects.all().delete()

        for fixture in  Command.FIXTURES:
            call_command('loaddata', fixture)
