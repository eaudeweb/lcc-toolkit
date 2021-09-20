from django.core.management.base import BaseCommand
from lcc.models import Gap, Legislation, LegislationSection
import lorem


class Command(BaseCommand):

    help = "Generate sections for testing purpose"

    def handle(self, *args, **options):
        gaps = Gap.objects.all()
        try:
            legislation = Legislation.objects.all()[0]
        except IndexError:
            print("Add a legislation before running this command")
            return

        for idx, gap in enumerate(gaps):
            section = LegislationSection.objects.create(
                text=lorem.text(),
                legislation=legislation,
                legislation_page=1,
                code=idx,
            )
            section.classifications = gap.classifications.all()
            section.tags = gap.tags.all()
            section.save()

        print("Random sections created")
