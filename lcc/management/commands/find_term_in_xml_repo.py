import re
import requests
from bs4 import BeautifulSoup

from django.db.models import Q
from django.core.management.base import BaseCommand

from lcctoolkit.settings.base import (
    LEGISPRO_URL,
    LEGISPRO_USER,
    LEGISPRO_PASS,
    UNHABITAT_URL,
    UNFAO_URL,
)
from lcc.models import Country


class Command(BaseCommand):

    help = "Find term in all LegisPro legislations"

    def add_arguments(self, parser):
        parser.add_argument(
            "--commonwealth",
            action="store_true",
            help="Use commonwealth repository (enabled by default)",
        )
        parser.add_argument(
            "--unfao",
            action="store_true",
            help="Use FAO repository",
        )
        parser.add_argument(
            "--unhabitat",
            action="store_true",
            help="Use UN Habitat repository",
        )
        parser.add_argument(
            "--term", action="store", help="Term to find in legislation"
        )

    def parse_country(self, legislation_data):
        title = legislation_data.find("frbrcountry")
        iso_code = title.get("value") if title else ""
        if not iso_code:
            return ""
        if iso_code == "GB":
            return Country.objects.filter(iso_code="UK").first()
        else:
            return Country.objects.filter(Q(iso_code=iso_code) | Q(pk=iso_code)).first()

    def parse_year(self, legislation_data):
        title = legislation_data.find("frbrname")
        year = re.findall("\d{4}", title.get("value")) if title else ""
        if year:
            return year[0]
        # Specific fix for The New York Community Risk And Resiliency Act
        return "2014"

    def parse_legislation_data(self, legislation_data, legispro_article):
        title = legislation_data.find("frbrname")
        legislation_dict = {
            "title": title.get("value") if title else "",
            "country": self.parse_country(legislation_data),
            "year": self.parse_year(legislation_data),
            "legispro_article": legispro_article,
            "import_from_legispro": True,
        }
        return legislation_dict

    def find_in_legislation(self, legislation_origin, legislation_url, term):
        legislation_link = "/".join([legislation_url, legislation_origin])
        response = requests.get(
            legislation_link,
            auth=requests.auth.HTTPBasicAuth(LEGISPRO_USER, LEGISPRO_PASS),
        )
        legislation_data = BeautifulSoup(response.content, "lxml")

        fields = self.parse_legislation_data(legislation_data, legislation_origin)
        print("Parsing legislation {} {}".format(legislation_origin, fields["title"]))

        # Search in legislation-wide tags
        for concept in legislation_data.find_all("TLCConcept"):
            title = concept.get("showas")
            if title and term in title:
                print(
                    "Matching legislation-wide concept {} in legislation "
                    "{}".format(fields["title"], title)
                )

        # Search in normal concept tags
        for concept in legislation_data.find_all("concept"):
            title = concept.get("title")
            if title and term in title:
                print(
                    "Matching concept {} in legislation {}".format(
                        fields["title"], title
                    )
                )

        # Search in article tags, as they can also have concepts
        possible_article_tags = (
            "article",
            "section",
            "chapter",
            "part",
        )
        for tag in possible_article_tags:
            for item in legislation_data.find_all(tag):
                refers_to = item.get("refersto")
                if not refers_to:
                    continue
                title = item.get("title")
                if title and term in title:
                    print(
                        "Matching concept {} in legislation {}".format(
                            fields["title"], title
                        )
                    )

    def handle(self, *args, **options):
        legislation_url = LEGISPRO_URL
        if options["unfao"]:
            legislation_url = UNFAO_URL
        if options["unhabitat"]:
            legislation_url = UNHABITAT_URL

        if not options["term"]:
            print("A search term must be provided. Exiting.")
            return

        print("Searching for term {} in all legislation.".format(options["term"]))

        response = requests.get(
            legislation_url,
            auth=requests.auth.HTTPBasicAuth(LEGISPRO_USER, LEGISPRO_PASS),
        )
        xml_soup = BeautifulSoup(response.content, "lxml")
        legislation_resources = xml_soup.find_all("exist:resource")

        for legislation_resource in legislation_resources:
            self.find_in_legislation(
                legislation_resource.get("name"), legislation_url, options["term"]
            )
