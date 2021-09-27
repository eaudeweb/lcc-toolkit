from openpyxl import Workbook, load_workbook

from django.core.management import call_command
from django.core.management.base import BaseCommand

from lcc.models import (
    TaxonomyClassification,
    Question,
    Gap,
)


class Command(BaseCommand):

    help = """
        Import Questions and Gaps from an excel file.
        File example in commands/example/questions.xlsx
    """

    def add_arguments(self, parser):
        parser.add_argument("file", type=str)
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Only parse the data, but do not insert it.",
        )

    def parse_row(self, row):
        return {
            "text": row[0].value.strip(),
            "level": row[1].value,
            "parent_answer": row[2].value,
            "classification": row[3].value,
            "gap_answer": row[4].value,
            "gap_classifications": str(row[5].value).split(","),
        }

    def create_question(self, data, parents_by_level):
        if data["level"] == 0:
            parent = None
        else:
            parent = parents_by_level[data["level"] - 1]
        classification = TaxonomyClassification.objects.get(code=data["classification"])
        question = Question.objects.filter(
            classification=classification, parent=parent
        ).first()
        if question:
            parents_by_level[data["level"]] = question
            print("Question for {} already created.".format(classification))
            return
        print("Creating question for {} with parent {}".format(classification, parent))
        if not options["dry_run"]:
            question = Question.objects.create(
                text=data["text"],
                parent=parent,
                parent_answer=data["parent_answer"],
                classification=classification,
            )
            return question

    def create_gap(self, data, question):
        gap_classifications = []
        for code in data["gap_classifications"]:
            classification = TaxonomyClassification.objects.get(code=code)
            gap_classifications.append(classification)

        gap = Gap.objects.create(on=data["gap_answer"], question=question)
        for classification in gap_classifications:
            gap.classifications.add(classification)

    def handle(self, file, *args, **options):
        wb = load_workbook(file, read_only=True)
        sheet = wb.active
        parents_by_level = [None] * 10
        for row in sheet:
            data = self.parse_row(row)
            try:
                question = self.create_question(data, parents_by_level)
                if not question:
                    continue
                parents_by_level[data["level"]] = question
                self.create_gap(data, question)
            except Exception as e:
                print(
                    "Failed to create question for {} with error {}".format(
                        data["classification"], str(e)
                    )
                )
