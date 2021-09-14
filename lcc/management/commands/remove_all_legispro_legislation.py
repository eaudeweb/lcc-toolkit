from random import randint, shuffle

from django.core.management.base import BaseCommand

from lcc.models import Legislation


class Command(BaseCommand):

    help = "Remove all legislation taken from LegisP§ro server"

    def handle(self, *args, **options):
        ELASTICSEARCH_DSL_AUTO_REFRESH = False
        legislations = Legislation.objects.filter(import_from_legispro=True)
        for legislation in legislations:
            print(f"Removed {legislation.title} legislations imported from legispro.")
            legislation.delete()
