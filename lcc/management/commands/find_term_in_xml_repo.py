import requests
from bs4 import BeautifulSoup

from django.core.management.base import BaseCommand

from lcctoolkit.settings.base import (
    LEGISPRO_URL,
    LEGISPRO_USER,
    LEGISPRO_PASS,
    UNHABITAT_URL,
    UNFAO_URL,
)


class Command(BaseCommand):

    help = "Find term in all LegisPro legislations"

    def add_arguments(self, parser):
        parser.add_argument(
            '--commonwealth',
            action='store_true',
            help='Use commonwealth repository (enabled by default)',
        )
        parser.add_argument(
            '--unfao',
            action='store_true',
            help='Use FAO repository',
        )
        parser.add_argument(
            '--unhabitat',
            action='store_true',
            help='Use UN Habitat repository',
        )
        parser.add_argument(
            '--term',
            action='store',
            help='Term to find in legislation'
        )

    def parse_legislation_data(self, legislation_data, legispro_article):
        legislation_dict = {
            'title': legislation_data.find('frbrname').get('value'),
            'country': self.parse_country(legislation_data),
            'year': self.parse_year(legislation_data),
            'legispro_article': legispro_article,
            'import_from_legispro': True
        }
        return legislation_dict

    def find_in_legislation(self, legislation_origin, legislation_url, term):
        legislation_link = '/'.join([legislation_url, legislation_origin])
        response = requests.get(
            legislation_link,
            auth=requests.auth.HTTPBasicAuth(LEGISPRO_USER, LEGISPRO_PASS)
        )
        legislation_data = BeautifulSoup(response.content, 'lxml')

        fields = self.parse_legislation_data(
            legislation_data, legislation_origin
        )
        print('Parsing legislation {} {}'.format(
            legislation_origin, fields['title'])
        )

        for concept in legislation_data.find_all('concept'):
            title = concept.get('title')
            if term in title:
                print(
                    'Matching concept {} in legislation {}'.format(
                        fields['title'], title
                    )
                )

    def handle(self, *args, **options):
        legislation_url = LEGISPRO_URL
        if options['unfao']:
            legislation_url = UNFAO_URL
        if options['unhabitat']:
            legislation_url = UNHABITAT_URL

        if not options['term']:
            print('A search term must be provided. Exiting.')
            return

        response = requests.get(
            legislation_url,
            auth=requests.auth.HTTPBasicAuth(LEGISPRO_USER, LEGISPRO_PASS)
        )
        xml_soup = BeautifulSoup(response.content, 'lxml')
        legislation_resources = xml_soup.find_all("exist:resource")

        for legislation_resource in legislation_resources:
            self.find_in_legislation(
                legislation_resource.get('name'),
                legislation_url,
                options['term']
            )

