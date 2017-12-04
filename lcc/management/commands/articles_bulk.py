import logging
from functools import partial
from itertools import takewhile
import openpyxl

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from lcc import models

LOGGER = logging.getLogger(__name__)


def _row_value(idx, row):
    return row[idx].value


LAW_NAME = partial(_row_value, 0)
LAW_PK = partial(_row_value, 1)
ARTICLE_TEXT = partial(_row_value, 2)
ARTICLE_CODE = partial(_row_value, 3)
LAW_PAGE = partial(_row_value, 4)
CLASSIFICATIONS = partial(_row_value, 5)
TAGS = partial(_row_value, 6)

classfications_dict = {
    classification.code: classification.pk
    for classification in models.TaxonomyClassification.objects.all()
}


def get_classfications(cls_tax):
    if isinstance(cls_tax, float):
        return [classfications_dict[str(cls_tax)]]
    if isinstance(cls_tax, str):
        cls_list = cls_tax.split('; ')
        return [classfications_dict[code] for code in cls_list]
    if cls_tax is None:
        return []


def get_tags(tags):
    if isinstance(tags, float):
        return [int(tags)]
    if isinstance(tags, str):
        tags_list = tags.split(';')
        return [int(tag) for tag in tags_list]
    if tags is None:
        return []


def import_row(row):
    text = ARTICLE_TEXT(row).replace("\r\n", '\n')
    text = text.replace("\\r\\n", '\n')

    article = models.LegislationArticle(
        text=text,
        legislation=models.Legislation.objects.get(pk=int(LAW_PK(row))),
        legislation_page=int(LAW_PAGE(row)),
        code=str(ARTICLE_CODE(row))
    )
    article.save()

    article.classifications = get_classfications(CLASSIFICATIONS(row))
    article.tags = get_tags(TAGS(row))
    article.save()

    LOGGER.info('Created %s', article.code)


class Command(BaseCommand):

    help = "Load articles data"

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str)

    @transaction.atomic
    def handle(self, *args, **options):
        if 'file_path' not in options:
            raise CommandError("File path is required")
        wb = openpyxl.load_workbook(options['file_path'], read_only=True)
        sh = wb['Sheet1']

        valid_rows = takewhile(lambda row: any(c.value for c in row), sh.rows)
        for idx, row in enumerate(valid_rows):
            if idx == 0:
                LOGGER.warning('Skipping header row.')
                continue
            import_row(row)
        LOGGER.info('Done!')
