import factory.fuzzy

from lcc.constants import ALL_LANGUAGES, GEOGRAPHICAL_COVERAGE, LEGISLATION_TYPE
from lcc.models import Country, Legislation


COUNTRIES = Country.objects.all()


class LegislationFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Legislation

    title = factory.LazyAttribute(
        lambda obj: factory.Faker('catch_phrase').generate({}) + ' law')
    abstract = factory.Faker('paragraph', nb_sentences=10)
    country = factory.fuzzy.FuzzyChoice(COUNTRIES)
    language = factory.fuzzy.FuzzyChoice(
        [tup[0] for tup in ALL_LANGUAGES])
    law_type = factory.fuzzy.FuzzyChoice(
        [tup[0] for tup in LEGISLATION_TYPE])
    # The amendment has to be in the past
    year_amendment = factory.fuzzy.FuzzyChoice(range(1901, 2018))
    # And the original year has to be before the amendment
    year = factory.LazyAttribute(
        lambda obj: (
            obj.year_amendment -
            factory.fuzzy.FuzzyChoice(range(10)).fuzz()
        )
    )

    geo_coverage = factory.fuzzy.FuzzyChoice(
        [tup[0] for tup in GEOGRAPHICAL_COVERAGE])

    # source?
    # source_type?

    website = factory.Faker('url')

    # pdf_file?
    # pdf_file_name?
