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


CW = partial(_row_value, 0)
SMALL_CW = partial(_row_value, 1)
UN = partial(_row_value, 2)
LDC = partial(_row_value, 3)
LLDC = partial(_row_value, 4)
SID = partial(_row_value, 5)
ISO3 = partial(_row_value, 6)
REGION = partial(_row_value, 7)
SUB_REGION = partial(_row_value, 8)
COUNTRY = partial(_row_value, 9)
LEGAL_SYSTEM = partial(_row_value, 10)
POPULATION = partial(_row_value, 11)
HDI2015 = partial(_row_value, 13)
GDP_CAPITA = partial(_row_value, 15)
GHG_NO_LUCF = partial(_row_value, 17)
GHG_LUCF = partial(_row_value, 19)
CVI2015 = partial(_row_value, 21)
FOCUS_AREAS = partial(_row_value, 22)
PRIORITY_SECTORS = partial(_row_value, 23)


def _stripped_values(value: str, split_on=';'):
    return tuple(map(str.strip, value.split(split_on)))


def _get_or_create(model, value):
    if value:
        obj, created = model.objects.get_or_create(name=value)
        if created:
            LOGGER.info('Created: %s', obj)
        else:
            LOGGER.info('Got: %s', obj)
        return obj


def _cast_or_default(cast, val, default=None):
    return cast(val) if val else default


def _with_row_value(func, val, default=None):
    return func(val) if val else default


def _models_from_value(model, value):
    split_values = _stripped_values(value) if value else tuple()
    return [_get_or_create(model, val) for val in split_values if val]


def _country_has_metadata(country):
    try:
        return models.CountryMetadata.objects.get(country=country)
    except models.CountryMetadata.DoesNotExist:
        return None


def create_metadata(country, row):
    metadata = models.CountryMetadata(
        country=country,
        cw=bool(CW(row)),
        small_cw=bool(SMALL_CW(row)),
        un=bool(UN(row)),
        ldc=bool(LDC(row)),
        lldc=bool(LLDC(row)),
        sid=bool(SID(row)),
        population=_cast_or_default(float, POPULATION(row)),
        hdi2015=_cast_or_default(float, HDI2015(row)),
        gdp_capita=_cast_or_default(float, GDP_CAPITA(row)),
        ghg_no_lucf=_cast_or_default(float, GHG_NO_LUCF(row)),
        ghg_lucf=_cast_or_default(float, GHG_LUCF(row)),
        cvi2015=_cast_or_default(float, CVI2015(row)),
    )
    metadata.save()
    return metadata


def import_row(row):

    country, created = models.Country.objects.get_or_create(
        iso=ISO3(row),
        defaults=dict(name=COUNTRY(row).strip()),
    )

    if created:
        LOGGER.info('Created country: %s', country)
    else:
        LOGGER.info('Got country: %s', country)

    existing = _country_has_metadata(country)
    if existing:
        LOGGER.warning('Skipping row. Metadata already exists: %s', existing)
        return

    region = _get_or_create(models.Region, REGION(row).strip())

    sub_region = _get_or_create(
        models.SubRegion,
        _with_row_value(str.strip, SUB_REGION(row)),
    )

    legal_system = _get_or_create(
        models.LegalSystem,
        _with_row_value(str.strip, LEGAL_SYSTEM(row)),
    )

    focus_areas = _models_from_value(
        models.FocusArea,
        FOCUS_AREAS(row)
    )

    priority_sectors = _models_from_value(
        models.PrioritySector,
        PRIORITY_SECTORS(row),
    )

    metadata = create_metadata(country, row)

    # assign many to many fields
    metadata.region = region
    metadata.sub_region = sub_region
    metadata.legal_system = legal_system
    metadata.mitigation_focus_areas = (
        focus_areas if focus_areas else []
    )
    metadata.adaptation_priority_sectors = (
        priority_sectors if priority_sectors else []
    )

    metadata.save()

    LOGGER.info('Created: %s', metadata)


class Command(BaseCommand):

    help = "Load intial data"

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

            if not ISO3(row):
                LOGGER.warning('Skipping row without ISO: %s', idx)
                continue

            import_row(row)

        LOGGER.info('Done!')
