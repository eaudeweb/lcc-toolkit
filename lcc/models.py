import math
import time
import pdftotext
import pycountry
import mptt.models

from copy import deepcopy
from operator import itemgetter
from rolepermissions.roles import get_user_roles

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.db import models, transaction
from django.db.models import F, Subquery, OuterRef
from django.db.models.signals import m2m_changed
from django.urls import reverse
from django.utils.safestring import mark_safe

import lcc.utils as utils
import lcc.constants as constants


User = get_user_model()


POP_RANGES = (
    (0, 299),
    (300, 1499),
    (1500, 3999),
    (4000, 5999),
    (6000, 9999),
    (10000, 19999),
    (20000, 39999),
    (40000, 99999),
    (100000, math.inf),
)

HDI_RANGES = (
    (0.350, 0.470),
    (0.471, 0.501),
    (0.502, 0.563),
    (0.564, 0.607),
    (0.608, 0.649),
    (0.650, 0.693),
    (0.694, 0.730),
    (0.731, 0.754),
    (0.755, 0.782),
    (0.783, 0.807),
    (0.808, 0.848),
    (0.849, 0.884),
    (0.885, 0.915),
    (0.916, 0.949),
)

GDP_RANGES = (
    (0, 1005, 'Low'),
    (1006, 3955, 'Lower-middle'),
    (3956, 12235, 'Upper-middle'),
    (12236, math.inf, 'High'),
)


GHG_NO_LUCF = (
    (0, 0.99),
    (1, 9.99),
    (10, 24.99),
    (25, 49.99),
    (50, 99.99),
    (100, 299.99),
    (300, 999.99),
    (1000, math.inf)
)

GHG_LUCF = (
    (-math.inf, 0),
    (0, 0.99),
    (1, 9.99),
    (10, 24.99),
    (25, 49.99),
    (50, 99.99),
    (100, 299.99),
    (300, 999.99),
    (1000, math.inf)
)


def _format_range(range):
    min, max = range
    formatter = f'{min} - {max}'
    if max == math.inf:
        formatter = f'> {min}'
    if min == -math.inf:
        formatter = f'< {max}'
    return formatter


def _range_from_value(range, value):
    min, max = map(itemgetter, (0, 1))
    return next(
        val for val in range
        if min(val) <= value <= max(val)
    )


class TaxonomyTagGroup(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return 'Tagging by ' + self.name


class TaxonomyTag(models.Model):
    # NOTE: The name must not contain the character ";".
    name = models.CharField(max_length=255)
    group = models.ForeignKey(TaxonomyTagGroup, related_name='tags')

    def __str__(self):
        return "Tag " + self.name


class TaxonomyClassification(mptt.models.MPTTModel):
    # NOTE: The name must not contain the character ";".
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=16, unique=True, blank=True)
    parent = mptt.models.TreeForeignKey('self',
                                        null=True,
                                        blank=True,
                                        related_name='children')

    class Meta:
        verbose_name = 'Taxonomy Classification'
        verbose_name_plural = 'Taxonomy Classifications'
        ordering = ('code',)

    class MPTTMeta:
        order_insertion_by = ['code']

    @classmethod
    def _pre_save_classification_code_on_create(cls, instance):
        """Logic executed before saving a new TaxonomyClassification instance.
        Set the next code for the classification.
        """
        instance.code = utils.generate_code(cls, instance)

    @staticmethod
    def _pre_save_classification_code_on_edit(instance):
        """Logic executed before editing an TaxonomyClassification instance.

        Update the code for every child to match the parent classification.
        """
        for classification in instance.children.all():
            parts = classification.code.split('.')
            suffix_code = parts[-1]
            classification.code = '{0}.{1}'.format(instance.code, suffix_code)
            classification.save()

    @staticmethod
    def pre_save_classification_code(**kwargs):

        instance = kwargs['instance']

        if instance.code:
            TaxonomyClassification._pre_save_classification_code_on_edit(
                instance)
        else:
            TaxonomyClassification._pre_save_classification_code_on_create(
                instance)

    def get_classification_level(self):
        # The logical classification of taxonomy starts from 1
        # The tree level of an object starts from 0
        return self.get_level() + 1

    def __str__(self):
        return "{} classification: {}".format(
            self.code, self.name
        )


models.signals.pre_save.connect(
    TaxonomyClassification.pre_save_classification_code,
    sender=TaxonomyClassification
)


class _TaxonomyModel(models.Model):
    classifications = models.ManyToManyField(
        TaxonomyClassification, blank=True)
    tags = models.ManyToManyField(
        TaxonomyTag, blank=True)

    _classification_ids = ArrayField(
        models.IntegerField(), default=list, blank=True)
    _tag_ids = ArrayField(
        models.IntegerField(), default=list, blank=True)

    class Meta:
        abstract = True
        indexes = [GinIndex(fields=['_classification_ids']),
                   GinIndex(fields=['_tag_ids'])]

    """
    # this is what we'd like to do, but m2m operations don't pass through save
    def save(self, *args, **kwargs):
        self._classification_ids = [c.id for c in self.classifications]
        self._tag_ids = [t.id for t in self.tags]

        super().save(*args, **kwargs)
    """


def cache_taxonomy(sender, **kwargs):
    # this is hard stuff to code, so avoiding it until really necessary:
    if kwargs['reverse']:
        raise RuntimeError("noway, like, really")

    watched = ('post_add', 'post_clear', 'post_remove')
    m2ms = {
        TaxonomyClassification: {
            'source': 'classifications',
            'target': '_classification_ids',
        },
        TaxonomyTag: {
            'source': 'tags',
            'target': '_tag_ids',
        },

    }

    if kwargs['action'] not in watched:
        return

    try:
        fields = m2ms[kwargs['model']]
    except KeyError:
        return

    instance = kwargs['instance']

    setattr(
        instance,
        fields['target'],
        [item.id for item in getattr(instance, fields['source']).all()])
    instance.save()


m2m_changed.connect(cache_taxonomy)


class Region(models.Model):
    name = models.CharField('Name', max_length=128)

    def __str__(self):
        return self.name

    def countries(self):
        return (
            obj.country for obj in
            self.countrymetadata_set.filter(
                user=None).only('country').select_related('country')
        )


class SubRegion(models.Model):
    name = models.CharField('Name', max_length=128)

    def __str__(self):
        return self.name


class LegalSystem(models.Model):
    name = models.CharField('Name', max_length=128)

    def __str__(self):
        return self.name


class FocusArea(models.Model):
    name = models.CharField('Name', max_length=255)

    def __str__(self):
        return self.name


class PrioritySector(models.Model):
    name = models.CharField('Name', max_length=255)

    def __str__(self):
        return self.name


class CountryMetadata(models.Model):
    """
    This model provides aditional information about a country.

    NOTE: For the application to work, it is necessary that at any given point
    there is exactly one CountryMetadata instance with user=None for every
    Country. However, this is only enforced at the application layer, so any
    incautious direct interventions (e.g. loading custom data, creating objects
    via shell, etc.) may leave the application in an inconsistent state.
    """

    country = models.ForeignKey('Country', related_name='metadata')
    user = models.ForeignKey('UserProfile', null=True)

    cw = models.BooleanField('Commonwealth (Member country)', default=False)
    small_cw = models.BooleanField('Small commonwealth country', default=False)
    un = models.BooleanField('United Nations (Member state)', default=False)
    ldc = models.BooleanField('Least developed country (LDC)', default=False)
    lldc = models.BooleanField(
        'Landlocked developing country (LLDC)',
        default=False
    )
    sid = models.BooleanField(
        'Small island developing state (SID)',
        default=False
    )

    region = models.ForeignKey(Region, null=True, blank=True)
    sub_region = models.ForeignKey(SubRegion, null=True, blank=True)
    legal_system = models.ForeignKey(LegalSystem, null=True, blank=True)

    population = models.FloatField("Population ('000s) 2018", null=True)
    hdi2015 = models.FloatField('HDI2015', null=True)

    gdp_capita = models.FloatField('GDP per capita, US$ 2016', null=True)
    ghg_no_lucf = models.FloatField(
        'Total GHG Emissions excluding LUCF MtCO2e 2014',
        null=True
    )
    ghg_lucf = models.FloatField(
        'Total GHG Emissions including LUCF MtCO2e 2014',
        null=True
    )
    cvi2015 = models.FloatField(
        'Climate vulnerability index 2015',
        null=True,
        blank=True
    )

    mitigation_focus_areas = models.ManyToManyField(
        FocusArea,
        blank=True
    )

    adaptation_priority_sectors = models.ManyToManyField(
        PrioritySector,
        blank=True
    )

    def __str__(self):
        return f'{self.country.name} ({self.user or "no user"})'

    def get_absolute_url(self):
        return reverse('lcc:country:view', kwargs={'iso': self.country.iso})

    @property
    def population_range(self):
        return _format_range(
            _range_from_value(POP_RANGES, self.population))

    @property
    def hdi2015_range(self):
        return (
            _format_range(_range_from_value(HDI_RANGES, self.hdi2015))
            if self.hdi2015 else 'N/A'
        )

    @property
    def gdp_capita_range(self):
        label = itemgetter(2)
        return (
            label(_range_from_value(GDP_RANGES, self.gdp_capita))
            if self.gdp_capita else 'N/A'
        )

    @property
    def ghg_no_lucf_range(self):
        return (
            _format_range(_range_from_value(GHG_NO_LUCF, self.ghg_no_lucf))
            if self.ghg_no_lucf else None
        )

    @property
    def ghg_lucf_range(self):
        return (
            _format_range(_range_from_value(GHG_LUCF, self.ghg_lucf))
            if self.ghg_lucf else None
        )

    def clone_to_profile(self, user_profile):
        # copy original
        clone = deepcopy(self)
        clone.pk = None
        clone.user = user_profile

        clone.save()

        # copy many to many fields
        m2m = (
            f.name for f in self._meta.get_fields()
            if isinstance(f, models.ManyToManyField)
        )

        for name in m2m:
            val = (
                getattr(self, name).all()
                if hasattr(self, name) else []
            )
            setattr(clone, name, val)

        clone.save()

        return clone


class Country(models.Model):
    iso = models.CharField('ISO', max_length=3, primary_key=True)
    name = models.CharField('Name', max_length=128)

    class Meta:
        verbose_name = 'Country'
        verbose_name_plural = 'Countries'
        ordering = ('name',)
        db_table = "country"

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    home_country = models.ForeignKey(
        Country, related_name='home_country', null=True)
    countries = models.ManyToManyField(Country)

    affiliation = models.CharField(
        'Institutional affiliation',
        max_length=255,
        null=True,
        blank=True,
    )

    position = models.CharField(
        'Position',
        max_length=255,
        null=True,
        blank=True,
    )

    @property
    def roles(self):
        return get_user_roles(self.user)

    @property
    def flag(self):
        """ Returns alpha3 from iso3.
        """
        return pycountry.countries.get(alpha_3=self.home_country.iso).alpha_3

    @property
    def country(self):
        if self.home_country is None:
            # @TODO  Please remove this when User management is added
            #      in the frontend.
            return "User without a country"
        return self.home_country.name

    def __str__(self):
        return self.user.username


class LegislationManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().select_related('country')


class Legislation(_TaxonomyModel):
    title = models.CharField(max_length=256)
    abstract = models.CharField(max_length=1024, blank=True, null=True)
    country = models.ForeignKey(Country, related_name="legislations")
    language = models.CharField(
        choices=constants.ALL_LANGUAGES,
        default=constants.DEFAULT_LANGUAGE,
        max_length=64
    )
    law_type = models.CharField(
        choices=constants.LEGISLATION_TYPE,
        default=constants.LEGISLATION_TYPE_DEFAULT,
        max_length=64
    )
    year = models.IntegerField(default=constants.LEGISLATION_YEAR_RANGE[-1])
    year_amendment = models.IntegerField(
        default=constants.LEGISLATION_DEFAULT_YEAR,
        blank=True,
        null=True
    )
    year_mention = models.CharField(max_length=1024, blank=True, null=True)
    geo_coverage = models.CharField(
        choices=constants.GEOGRAPHICAL_COVERAGE,
        default=constants.GEOGRAPHICAL_COVERAGE_DEFAULT,
        max_length=64,
        null=True
    )
    source = models.CharField(max_length=256, blank=True, null=True)
    source_type = models.CharField(
        choices=constants.SOURCE_TYPE,
        default=constants.SOURCE_TYPE_DEFAULT,
        max_length=64, blank=True, null=True
    )
    website = models.URLField(max_length=2000, blank=True, null=True)

    pdf_file = models.FileField(null=True)
    pdf_file_name = models.CharField(null=True, max_length=256)

    objects = LegislationManager()

    @property
    def country_name(self):
        return self.country.name

    @property
    def country_iso(self):
        return self.country.iso

    @property
    def other_legislations(self):
        other = {}
        for classification in self.classifications.all():
            other[classification] = Legislation.objects.filter(
                classifications__id__exact=classification.pk).exclude(pk=self.pk).all()[:3]
        return other

    # @TODO: Change the __str__ to something more appropriate
    def __str__(self):
        return "Legislation: " + ' | '.join([self.country.name, self.law_type])

    def highlighted_title(self):
        """
        If this law was returned as a result of an elasticsearch query, return
        the title with the search terms highlighted. If not, return the original
        title.
        """
        return getattr(self, '_highlighted_title', self.title)

    def highlighted_abstract(self):
        """
        If this law was returned as a result of an elasticsearch query, return
        the abstract with the search terms highlighted. If not, return an empty
        string.
        """
        return getattr(self, '_highlighted_abstract', '')

    def highlighted_pdf_text(self):
        """
        If this law was returned as a result of an elasticsearch query, return
        the pdf_text with the search terms highlighted. If not, return an empty
        string.
        """
        return getattr(self, '_highlighted_pdf_text', '')

    def highlighted_classifications(self):
        """
        If this law was returned as a result of an elasticsearch query, return
        a list of classification names with the search terms highlighted. If
        not, return the original list of classification names.
        """
        return getattr(
            self, '_highlighted_classifications',
            self.classifications.all().values_list('name', flat=True)
        )

    def highlighted_tags(self):
        """
        If this law was returned as a result of an elasticsearch query, return
        a list of tag names with the search terms highlighted. If not, return
        the original list of tag names.
        """
        return getattr(
            self, '_highlighted_tags',
            self.tags.all().values_list('name', flat=True)
        )

    def highlighted_articles(self):
        """
        If this law was returned as a result of an elasticsearch query, return
        a list of dictionaries representing articles with the search terms
        highlighted in the text field. If not, return an empty list.
        """
        return getattr(self, '_highlighted_articles', [])

    def save_pdf_pages(self):
        if settings.DEBUG:
            time_to_load_pdf = time.time()
        if settings.DEBUG:
            print("INFO: FS pdf file load time: %fs" %
                  (time.time() - time_to_load_pdf))
            time_begin_transaction = time.time()

        with transaction.atomic():
            pdf = pdftotext.PDF(self.pdf_file)
            for idx, page in enumerate(pdf):
                page = page.replace('\x00', '')
                LegislationPage(
                    page_text="<pre>%s</pre>" % page,
                    page_number=idx + 1,
                    legislation=self
                ).save()

        if settings.DEBUG:
            print("INFO: ORM models.LegislationPages save time: %fs" %
                  (time.time() - time_begin_transaction))

        # This is necessary in order to trigger the signal that will update the
        # ElasticSearch index.
        self.save()


class LegislationArticleManager(models.Manager):
    def get_articles_for_gaps(self, gap_ids):
        table = self.model._meta.db_table
        return self.select_related('legislation').extra(
            tables=['lcc_gap'],
            select={
                'gap_id': 'lcc_gap.id',
            },
            where=[
                "lcc_gap.id IN (%s)" % ','.join(map(str, gap_ids)),
                "%s._classification_ids @> lcc_gap._classification_ids" % table,
                "%s._tag_ids @> lcc_gap._tag_ids" % table
            ]
        )


class LegislationArticle(_TaxonomyModel):
    text = models.CharField(max_length=65535)
    legislation = models.ForeignKey(Legislation, related_name="articles")
    legislation_page = models.IntegerField()
    code = models.CharField(max_length=64)  # aka Article number

    objects = LegislationArticleManager()

    # @TODO: Change the __str__ to something more appropriate
    def __str__(self):
        return "Article: %s" % str(self.legislation)

    def classification_ids(self):
        return self.classifications.values_list('pk', flat=True)

    def tag_ids(self):
        return self.tags.values_list('pk', flat=True)


class LegislationPage(models.Model):
    page_text = models.CharField(max_length=65535)
    page_number = models.IntegerField()
    legislation = models.ForeignKey(Legislation, related_name="pages")

    def __str__(self):
        return "Page %d of Legislation %s" % (
            self.page_number, str(self.legislation.title)
        )


class Question(mptt.models.MPTTModel):

    text = models.CharField(max_length=1024)
    parent = mptt.models.TreeForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='children')
    parent_answer = models.NullBooleanField(default=None)
    order = models.IntegerField(blank=True)

    classification = models.ForeignKey(
        TaxonomyClassification,
        null=True, blank=True)

    class Meta:
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'

    class MPTTMeta:
        order_insertion_by = ['order']

    def save(self, *args, **kwargs):
        if not self.order:
            self.order = utils.set_order(self.classification, self.parent)
        super(Question, self).save(*args, **kwargs)

    @property
    def full_order(self):
        return ".".join([
            str(question.order)
            for question in self.get_ancestors(include_self=True)
        ])

    def __str__(self):
        if self.parent:
            return "Question: %s with parent answer: %s" % (
                self.full_order, self.parent_answer
            )
        else:
            return "C: %s Question: %s" % (self.classification.code, self.order)


class Gap(_TaxonomyModel):
    question = models.ForeignKey(Question, related_name="gaps")
    on = models.BooleanField()

    class Meta(_TaxonomyModel.Meta):
        unique_together = ('on', 'question')

    def __str__(self):
        return "Gap for Q %s" % self.question


class AssessmentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('country')


class Assessment(models.Model):
    user = models.ForeignKey(User, related_name="assessments")
    country = models.ForeignKey(Country, related_name="assessments")

    objects = AssessmentManager()

    class Meta:
        unique_together = ("user", "country")

    @property
    def country_name(self):
        return self.country.name

    @property
    def country_iso(self):
        return self.country.iso

    def __str__(self):
        return "%s' assessment for %s" % (
            self.user.username, self.country.name
        )


class AnswerManager(models.Manager):
    def get_assessment_answers(self, assessment_pk):
        answers = (
            self
            .select_related('question')
            .filter(assessment__pk=assessment_pk)
            .filter(value=F('question__gaps__on'))
            .annotate(gap_id=F('question__gaps__id'))
            .annotate(category_id=Subquery(
                Question.objects.filter(tree_id=OuterRef(
                    'question__tree_id'), parent=None)
                .values('classification_id')[:1]
            ))
        )

        return answers


class Answer(models.Model):
    assessment = models.ForeignKey(Assessment)
    question = models.ForeignKey(Question)
    value = models.BooleanField()

    objects = AnswerManager()

    class Meta:
        unique_together = ("question", "assessment")

    def __str__(self):
        return "Question %s for assessment %d" % (
            self.question.full_order, self.assessment.pk
        )
