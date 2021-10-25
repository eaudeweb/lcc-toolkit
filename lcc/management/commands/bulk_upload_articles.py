import logging
from functools import partial
from itertools import takewhile
import openpyxl
import re

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from lcc import models

LOGGER = logging.getLogger(__name__)


def _row_value(idx, row):
    return row[idx].value


IDENTIFIER = partial(_row_value, 0)
LAW_NAME = partial(_row_value, 3)
LAW_PK = partial(_row_value, 4)
LAW_PAGE = partial(_row_value, 5)
SECTION_CODE = partial(_row_value, 6)
SECTION_TEXT = partial(_row_value, 7)
TAGS = partial(_row_value, 8)
CLASSIFICATIONS = partial(_row_value, 9)

classfications_dict = {
    classification.code: classification.pk
    for classification in models.TaxonomyClassification.objects.all()
}


def get_classfications(cls_tax):
    if isinstance(cls_tax, float):
        return [classfications_dict[str(cls_tax)]]
    if isinstance(cls_tax, str):
        cls_list = re.split("; |;|, |,| ", cls_tax)
        return [
            classfications_dict[re.findall("(.*\d).*$", code)[0]]
            for code in cls_list
            if code != ""
        ]
    if cls_tax is None:
        return []


def get_tags(tags):
    if isinstance(tags, float) or isinstance(tags, int):
        return [int(tags)]
    if isinstance(tags, str):
        tags_list = re.split("; |;|, |,| ", tags)
        return [int(tag) for tag in tags_list if tag != ""]
    if tags is None:
        return []


def import_row(row):
    identifier = IDENTIFIER(row)

    if SECTION_TEXT(row) is None:
        LOGGER.warning("Skipping section {} (no text).".format(identifier))
        return
    classifications = get_classfications(CLASSIFICATIONS(row))
    tags = get_tags(TAGS(row))

    if (classifications == []) and (tags == []):
        LOGGER.warning("Skipping section {} (no taxonomy).".format(identifier))
        return

    text = SECTION_TEXT(row).replace("\r\n", "\n")
    text = text.replace("\\r\\n", "\n")

    print(identifier)

    section = models.LegislationSection(
        text=text,
        legislation=models.Legislation.objects.get(pk=int(LAW_PK(row))),
        legislation_page=int(LAW_PAGE(row)),
        code=str(SECTION_CODE(row)),
        identifier=int(identifier),
    )
    section.save()

    section.classifications = classifications
    section.tags = tags
    section.save()

    LOGGER.info("Created %s", section.code)


class Command(BaseCommand):

    help = "Load sections data"

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str)

    @transaction.atomic
    def handle(self, *args, **options):
        if "file_path" not in options:
            raise CommandError("File path is required")
        wb = openpyxl.load_workbook(options["file_path"], read_only=True)
        sh = wb["sections"]

        valid_rows = takewhile(lambda row: any(c.value for c in row), sh.rows)
        for idx, row in enumerate(valid_rows):
            if idx == 0:
                LOGGER.warning("Skipping header row.")
                continue
            import_row(row)
        LOGGER.info("Done!")
