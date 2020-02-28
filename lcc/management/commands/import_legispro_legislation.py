from datetime import datetime
import requests
import re

from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.db.models import Q

from lcctoolkit.settings.base import (
    LEGISPRO_URL,
    LEGISPRO_USER,
    LEGISPRO_PASS,
    UNHABITAT_URL,
    UNFAO_URL,
)

from lcc.constants import (
    ALL_LANGUAGES, 
    LEGISLATION_TYPE, 
    LEGISLATION_YEAR_RANGE
)
from lcc.models import (
    Country,
    Legislation,
    LegislationArticle,
    TaxonomyClassification,
)


sub_expression = '[^ a-zA-z.,:;()\'\-]+'


def find_classification(concept_name, concept_code):
    classification = TaxonomyClassification.objects.filter(
        legispro_code=concept_code
    ).first()
    if classification:
        return classification
    else:
        # Try to find classification by name instead; useful when
        # concepts in LegisPro have not been synced with our
        # TaxonomyClassifications.
        classification = TaxonomyClassification.objects.filter(
            name=concept_name
        )
        if classification.count() > 1:
            print(
                "More than one concept found for {} {}.".format(
                    concept_code, concept_name
                )
            )
            return None
        elif classification.count() == 0:
            print(
                "Concept {} {} not found.".format(
                    concept_code, concept_name
                )
            )
            return None
        else:
            return classification.first()


class Command(BaseCommand):

    help = "Import legislations from LegisPro"

    def add_arguments(self, parser):
        parser.add_argument(
            '--commonwealth',
            action='store_true',
            help='Use latest updated_at for updating or creating legislations',
        )
        parser.add_argument(
            '--use_last_update',
            action='store_true',
            help='Use latest updated_at for updating or creating legislations',
        )
        parser.add_argument(
            '--unfao',
            action='store_true',
            help='Use latest updated_at for updating or creating legislations',
        )
        parser.add_argument(
            '--unhabitat',
            action='store_true',
            help='Use latest updated_at for updating or creating legislations',
        )
        parser.add_argument(
            '--legislation',
            action='store',
            help='Import only the legislation from that link'
        )

    def parse_article(self, article, legislation):
        return {
            "code" : article.find('num').text.strip(),
            "text" : re.sub('^Article [0-9.]+[.]?', '',
                            article.text.strip()).strip().replace('\n\n', '\n'),
            "legislation" : legislation,
            "legispro_identifier": article.get('eid', '')
        }

    def add_concepts(self, concepts, article_object):
        article_object.classifications.clear()
        for concept in concepts:
            concept_name = re.sub(sub_expression, '' , concept.get('title')).strip()
            concept_code = concept.get("refersto").split("__")[1]
            classification = find_classification(concept_name, concept_code)
            if classification:
                article_object.classifications.add(classification)
                print(
                    'Added classification {} to article.'.format(
                        classification.code
                    )
                )

    def add_possible_concepts(self, possible_concepts, article_object):
        """
        Some concepts seem to be included in the "<level>" tag;
        we need to check that they have the "refersto" property.
        """
        for concept in possible_concepts:
            refers_to =  concept.get("refersto")
            if not refers_to:
                continue
            concept_name = re.sub(sub_expression, '' , concept.get('title')).strip()
            concept_code = refers_to.split("__")[1]
            classification = find_classification(concept_name, concept_code)
            if classification:
                article_object.classifications.add(classification)
                print(
                    'Added classification {} to article.'.format(
                        classification.code
                    )
                )

    def create_or_update_articles(self, legislation_data, legislation):
        articles = legislation_data.find_all('article')
        if not articles:
            # Fall back to looking for sections.
            articles = legislation_data.find_all('section')
        if not articles:
            # Then fall back to looking for chapters
            articles = legislation_data.find_all('chapter')
        if not articles:
            # And finally fall back to looking for parts.
            articles = legislation_data.find_all('part')
        for article in articles:
            try:
                fields = None
                fields = self.parse_article(article, legislation)
                article_objects = LegislationArticle.objects.filter(
                    legispro_identifier=fields['legispro_identifier'],
                    legislation=legislation
                )
                if article_objects:
                    article_objects.update(**fields)
                    article_object = article_objects.first()
                    print("Legislation {} - Article {} was updated.".format(
                        legislation.title,
                        fields['code']
                    ))
                else:
                    article_object = LegislationArticle.objects.create(**fields)
                    print("Legislation {} - Article {} was created.".format(
                        legislation.title,
                        fields['code']
                    ))
                # Add concepts that are included in the article tag
                self.add_possible_concepts([article, ], article_object)

                # Add concepts included in the article concepts
                self.add_concepts(article.find_all('concept'), article_object)
                self.add_possible_concepts(
                    article.find_all('level'), article_object
                )
            except Exception as e:
                if fields:
                    code = fields['code']
                else:
                    code = None
                print(
                    "Warning Legislation {} Article {} generated the folowing error: {}".format(
                        legislation.title, code, e)
                )

    def parse_country(self, legislation_data):
        iso_code = legislation_data.find('frbrcountry').get('value')
        if iso_code == 'GB':
            return Country.objects.filter(iso_code='UK').first()
        else:
            return Country.objects.filter(Q(iso_code=iso_code) | Q(pk=iso_code)).first()

    def parse_year(self, legislation_data):
        title = legislation_data.find('frbrname').get('value')
        year = re.findall('\d{4}', title)
        if year:
            return year[0]
        # Specific fix for The New York Community Risk And Resiliency Act
        return '2014'

    def parse_legislation_data(self, legislation_data, legispro_article):
        legislation_dict = {
            'title': legislation_data.find('frbrname').get('value'),
            'country': self.parse_country(legislation_data),
            'year': self.parse_year(legislation_data),
            'legispro_article': legispro_article,
            'import_from_legispro': True
        }
        return legislation_dict

    def add_legislation_concepts(self, legislation, legislation_object):
        legislation_object.classifications.clear()
        concepts = legislation.find_all('tlcconcept')
        for concept in concepts:
            concept_name = re.sub(sub_expression, '' , concept.get('showas')).strip()
            concept_code = concept.get("eid").split("__")[1]
            classification = find_classification(concept_name, concept_code)
            if classification:
                legislation_object.classifications.add(classification)
                print('Added classification {} to legislation.'.format(classification.code))

    def create_or_update_legislation(self, legislation_origin, legislation_url):
        legislation_link =  '/'.join([legislation_url, legislation_origin])
        response = requests.get(
            legislation_link, 
            auth=requests.auth.HTTPBasicAuth(LEGISPRO_USER, LEGISPRO_PASS)
        )
        legislation_data = BeautifulSoup(response.content, 'lxml')
        try:
            fields = None
            fields = self.parse_legislation_data(legislation_data, legislation_origin)
            if not fields['country']:
                print("Country {} was not found.".format(iso_code = legislation_data.find('frbrcountry').get('value')))
                return

            legislation = Legislation.objects.filter(legispro_article=legislation_origin)
            if legislation:
                legislation.update(**fields)
                legislation = legislation.first()
                print("Legislation {} was updated.".format(legislation.title))
            else:
                legislation = Legislation.objects.create(**fields)
                print("Legislation {} was created.".format(legislation.title))
            self.create_or_update_articles(legislation_data, legislation)
            self.add_legislation_concepts(legislation_data, legislation)
        except Exception as e:
            if fields:
                name = fields['title']
            else:
                name = None
            print("Warning Legislation {} generated the folowing error: {}".format(name, e))

    def must_update_legislation(self, legislation_resource, last_updated_date):
        try:
            legislation_last_updated = datetime.strptime(
                legislation_resource.get('last-modified'),
                '%Y-%m-%dT%H:%M:%S.%fZ'
            )
            return legislation_last_updated > last_updated_date
        except:
            return True

    def handle(self, *args, **options):
        legislation_url = LEGISPRO_URL
        if options['unfao']:
            legislation_url = UNFAO_URL
        if options['unhabitat']:
            legislation_url = UNHABITAT_URL

        print("Pulling data from {}".format(legislation_url))
        if options['legislation']:
            self.create_or_update_legislation(options['legislation'], legislation_url)
            return
        
        response = requests.get(
            legislation_url, auth=requests.auth.HTTPBasicAuth(LEGISPRO_USER, LEGISPRO_PASS)
        )
        xml_soup = BeautifulSoup(response.content, 'lxml')
        legislation_resources = xml_soup.find_all("exist:resource")

        if options['use_last_update']:
            last_updated_date = Legislation.objects.order_by('-date_updated').first().date_updated.replace(tzinfo=None)
            print("Using last update: {}".format(last_updated_date))

        for legislation_resource in legislation_resources:
            if not options['use_last_update']:
                self.create_or_update_legislation(legislation_resource.get('name'), legislation_url)
                continue

            if self.must_update_legislation(legislation_resource, last_updated_date):
                self.create_or_update_legislation(legislation_resource.get('name'), legislation_url)
