from openpyxl import load_workbook

from django.core.management.base import BaseCommand

from lcc.models import TaxonomyClassification


class Command(BaseCommand):

    help = """
        Import TaxonomyClassifcation from an excel file.
        File example in commands/example/taxonomy.xlsx
    """

    def add_arguments(self, parser):
        parser.add_argument('file', type=str)

    def handle(self, file, *args, **options):
        wb = load_workbook(file, read_only=True)
        sheet = wb.active
        for row in sheet:
            if not row[0].value:  # Empty row, ignore it
                continue
            code = str(row[0].value).strip()
            name = row[1].value.strip()
            parent_code = ".".join(code.split('.')[:-1])
            try:
                if code.find('.') == -1:
                    parent = None
                else:
                    parent = TaxonomyClassification.objects.get(code=parent_code)
                TaxonomyClassification.objects.create(
                    code=code,
                    name=name,
                    parent=parent
                )
            except Exception as e:
                print("Failed to create {} with error {}".format(name, str(e)))
