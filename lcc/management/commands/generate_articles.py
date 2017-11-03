from django.core.management.base import BaseCommand
from lcc.models import (
    Gap, Legislation, LegislationArticle
)
import lorem


class Command(BaseCommand):

    help = "Generate articles for testing purpose"

    def handle(self, *args, **options):
        gaps = Gap.objects.all()
        try:
            legislation = Legislation.objects.all()[0]
        except IndexError:
            print("Add a legislation before running this command")
            return

        for idx, gap in enumerate(gaps):
            article = LegislationArticle.objects.create(
                text=lorem.text(),
                legislation=legislation,
                legislation_page=1,
                code=idx,
            )
            article.classifications = gap.classifications.all()
            article.tags = gap.tags.all()
            article.save()

        print("Random articles created")
