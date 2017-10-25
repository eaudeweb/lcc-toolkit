import xlrd
from lcc.constants import LEGAL_SYSTEMS
from django.core.management.base import BaseCommand, CommandError
from lcc.models import Country


class Command(BaseCommand):

    help = "Load intial data"

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str)

    def handle(self, *args, **options):
        if 'file_path' not in options:
            raise CommandError("File path is required")
        wb = xlrd.open_workbook(options['file_path'])
        sh = wb.sheet_by_index(0)

        for i in range(1, 231):
            cw = True if sh.cell(i, 0).value else False
            small_cw = True if sh.cell(i, 1).value else False
            un = True if sh.cell(i, 2).value else False
            ldc = True if sh.cell(i, 3).value else False
            lldc = True if sh.cell(i, 4).value else False
            sid = True if sh.cell(i, 5).value else False
            iso3 = sh.cell(i, 6).value
            region = sh.cell(i, 7).value
            sub_region = sh.cell(i, 8).value
            name = sh.cell(i, 9).value
            # legal_system = sh.cell(i, 10).value
            population = sh.cell(i, 11).value
            hdi_2015 = sh.cell(i, 12).value if sh.cell(i, 12).value else None
            gdp = sh.cell(i, 12).value if sh.cell(i, 13).value else None
            ghg_excluding = sh.cell(i, 12).value if sh.cell(
                i, 14).value else None
            ghg_including = sh.cell(i, 12).value if sh.cell(
                i, 15).value else None
            climate_vulnerability = sh.cell(
                i, 12).value if sh.cell(i, 16).value else None

            for legal in LEGAL_SYSTEMS:
                if legal[1] == sh.cell(i, 10).value:
                    legal_system = legal[0]
                    break

            Country.objects.create(
                cw=cw,
                small_cw=small_cw,
                un=un,
                ldc=ldc,
                lldc=lldc,
                sid=sid,
                iso3=iso3,
                region=region,
                sub_region=sub_region,
                name=name,
                legal_system=legal_system,
                population=population,
                hdi_2015=hdi_2015,
                gdp=gdp,
                ghg_excluding=ghg_excluding,
                ghg_including=ghg_including,
                climate_vulnerability=climate_vulnerability
            )
