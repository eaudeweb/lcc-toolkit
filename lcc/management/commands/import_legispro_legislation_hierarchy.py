import re
import requests
import sys
import traceback
from bs4 import BeautifulSoup
from datetime import datetime
import xml.etree.ElementTree as ET

from django.core.management.base import BaseCommand
from django.db.models import Q

from lcctoolkit.settings.base import (
    LEGISPRO_URL,
    LEGISPRO_USER,
    LEGISPRO_PASS,
    UNHABITAT_URL,
    UNFAO_URL,
)
from lcc.models import (
    Country,
    Legislation,
    LegislationArticleTree,
    TaxonomyClassification,
)


sub_expression = "[^ a-zA-z,:;()\'\-]+"

# Tags that might be used for marking articles, in order of precedence.
possible_article_tags = ('article', 'section', 'chapter', 'part',)

def check_alphanumeric_classification_names(concept_name):
    classifications = TaxonomyClassification.objects.values_list("code", "name")
    for classification in classifications:
        if re.sub('[^A-Za-z0-9]+', '', classification[1]) == re.sub('[^A-Za-z0-9]+', '', concept_name):
            return TaxonomyClassification.objects.filter(code=classification[0])
    return None

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
            classification = check_alphanumeric_classification_names(concept_name)
            if classification:
                return classification.first()
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
            help='Use commonwealth repository (enabled by default)',
        )
        parser.add_argument(
            '--use_last_update',
            action='store_true',
            help='Use latest updated_at for updating or creating legislations',
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
            '--legislation',
            action='store',
            help='Import only the legislation from that link'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only parse the data and display what the script would do, '
                 'but do not touch the database.'
        )

    def parse_article(self, article, legislation, parent,code):
        text = ''
        for tag in article.find_all():
            if tag.get('guid'):
                break
            text = " ".join([text] +  tag.get_text().split())
        return {
            "code": code or article.find('num').text.strip(),
            "text": text,
            "legislation": legislation,
            "legispro_identifier": article.get('eid', ''),
            "parent": parent,
        }

    def add_concepts(self, concepts, article_object, dry_run=False):
        article_object.classifications.clear()
        for concept in concepts:
            concept_name = re.sub(
                sub_expression, '', concept.get('title')
            ).strip()
            concept_code = concept.get("refersto").split("__")
            concept_code = concept_code[1] \
                if (concept_code and len(concept_code) > 1) else ""
            classification = find_classification(concept_name, concept_code)
            if classification:
                if not dry_run:
                    article_object.classifications.add(classification)
                print(
                    'Added classification {} to article.'.format(
                        classification.code
                    )
                )

    def add_possible_concepts(
            self, possible_concepts, article_object, dry_run=False
    ):
        """
        Some concepts seem to be included in the sections tags;
        we need to check that they have the "refersto" property.
        """
        for concept in possible_concepts:
            refers_to = concept.get("refersto")
            if not refers_to:
                continue
            concept_name = re.sub(
                sub_expression, '', concept.get('title')
            ).strip()
            concept_code = refers_to.split("__")
            concept_code = concept_code[1] \
                if (concept_code and len(concept_code) > 1) else ""
            classification = find_classification(concept_name, concept_code)
            if classification:
                if not dry_run:
                    article_object.classifications.add(classification)
                article_code = article_object.code if article_object else ''
                print(
                    'Added classification {} to article {}.'.format(
                        classification.code, article_code
                    )
                )

    def find_children(self, legislation_data, section):
        return section.find_all(guid=True, recursive=False)

    def create_section(self, legislation_data, legislation, article, dry_run, parent=None, code=None):
        # create_section
        print(code)
        fields = None
        fields = self.parse_article(article, legislation, parent, code)
        article_objects = LegislationArticleTree.objects.filter(
            legispro_identifier=fields['legispro_identifier'],
            legislation=legislation,
            code=code,
        )
        if article_objects:
            article_objects.delete()
        article_object = LegislationArticleTree.objects.create(**fields)
        print("Legislation {} - Article {} was created.".format(legislation.title, fields['code']))
        self.add_possible_concepts([article, ], article_object, dry_run)
        # Add concepts included in the article concepts
        self.add_concepts(
            article.find_all('concept'), article_object, dry_run
        )

        #create section

        children = self.find_children(legislation_data, article)
        for idx, child in enumerate(children):
            next_code = f"{code}.{idx}"
            self.create_section(legislation_data, legislation, child, parent=article_object, dry_run=dry_run, code=next_code)
 
    def create_articles_tree(
            self, legislation_data, legislation, dry_run=False
    ):
        articles_root = legislation_data.find('body').find_all(guid=True, recursive=False)
        if not articles_root:
            print(
                'No articles found for legislation {}.'.format(
                    legislation.title
                )
            )
        
        for idx, article in enumerate(articles_root):
            self.create_section(legislation_data, legislation, article, dry_run=dry_run, parent=None, code=str(idx))

    def parse_country(self, legislation_data):
        iso_code = legislation_data.find('frbrcountry').get('value')
        iso_code = iso_code.split("-")[0] if "-" in iso_code else iso_code
        if iso_code == 'GB':
            return Country.objects.filter(iso_code='UK').first()
        elif iso_code == 'KHR':
            return Country.objects.filter(iso_code='KH').first()
        elif iso_code == 'TAN':
            return Country.objects.filter(iso_code='TZ').first()
        elif iso_code == 'PHI':
            return Country.objects.filter(iso_code='PH').first()
        elif iso_code == 'BER':
            return Country.objects.filter(iso_code='BM').first()
        elif iso_code == 'BRZ':
            return Country.objects.filter(iso_code='BR').first()
        else:
            return Country.objects.filter(
                Q(iso_code=iso_code) | Q(pk=iso_code)
            ).first()

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

    def add_legislation_concepts(
            self, legislation, legislation_object, dry_run
    ):
        if not dry_run:
            legislation_object.classifications.clear()
        concepts = legislation.find_all('tlcconcept')
        for concept in concepts:
            concept_name = re.sub(
                sub_expression, '' , concept.get('showas')
            ).strip()
            concept_code = concept.get("eid").split("__")

            concept_code = concept_code[1] \
                if (concept_code and len(concept_code) > 1) else ""
            classification = find_classification(concept_name, concept_code)
            if classification:
                if not dry_run:
                    legislation_object.classifications.add(classification)
                print(
                    'Added classification {} to legislation.'.format(
                        classification.code
                    )
                )
    
    def delete_articles(self, legislation):
        legislation.articles.delete()
        return

    def create_or_update_legislation(
        self, legislation_origin, legislation_url, dry_run=False
    ):
        """
        Creates or updates legislation.
        If `dry_run` parameter is set to True, will only display what it should
        be doing, without actually adding data to the database.
        """
        legislation_link = '/'.join([legislation_url, legislation_origin])
        response = requests.get(
            legislation_link, 
            auth=requests.auth.HTTPBasicAuth(LEGISPRO_USER, LEGISPRO_PASS)
        )
        legislation_data = BeautifulSoup(response.content, 'html.parser')
        try:
            fields = None
            fields = self.parse_legislation_data(
                legislation_data, legislation_origin
            )
            if not fields['country']:
                code = legislation_data.find('frbrcountry').get('value')
                print("Country {} was not found.".format(code))
                return

            legislation = Legislation.objects.filter(
                legispro_article=legislation_origin
            )
            if legislation.count() > 1:
                print(
                    'Warning: more than 1 legislation found for {}'.format(
                        legislation_origin
                    )
                )
            if legislation:
                if not dry_run:
                    legislation.update(**fields)
                    self.delete_articles(legislation)
                legislation = legislation.first()
                print("Legislation {} was updated.".format(fields['title']))
            else:
                if not dry_run:
                    legislation = Legislation.objects.create(**fields)
                print(
                    "Legislation {} was created.".format(fields['title'])
                )
            # Now also add articles and concepts
            self.create_articles_tree(
                legislation_data, legislation, dry_run
            )
            self.add_legislation_concepts(
                legislation_data, legislation, dry_run
            )
        except Exception as e:
            exc_info = sys.exc_info()
            if fields:
                name = fields.get("title", "")
            else:
                name = None
            print(
                "Warning Legislation {} generated the following error: \n"
                "{}".format(name, traceback.print_exception(*exc_info))
            )

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
            self.create_or_update_legislation(
                options['legislation'], legislation_url
            )
            return

        response = requests.get(
            legislation_url,
            auth=requests.auth.HTTPBasicAuth(LEGISPRO_USER, LEGISPRO_PASS)
        )
        xml_soup = BeautifulSoup(response.content, 'lxml')
        legislation_resources = xml_soup.find_all("exist:resource")

        if options['use_last_update']:
            last_updated_date = Legislation.objects.order_by(
                '-date_updated'
            ).first().date_updated.replace(tzinfo=None)
            print("Using last update: {}".format(last_updated_date))

        for legislation_resource in legislation_resources:
            if legislation_resource.get('name') == '.project.xml':
                continue

            if not options['use_last_update']:
                self.create_or_update_legislation(
                    legislation_resource.get('name'),
                    legislation_url,
                    options['dry_run']
                )
                continue

            must_update = self.must_update_legislation(
                legislation_resource, last_updated_date
            )
            if must_update:
                self.create_or_update_legislation(
                    legislation_resource.get('name'),
                    legislation_url,
                    options['dry_run']
                )
