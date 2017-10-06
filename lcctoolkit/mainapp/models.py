import mptt.models
import lcctoolkit.mainapp.utils as utils
import lcctoolkit.mainapp.constants as constants

from django.contrib import auth
from django.db import models
from django.dispatch import receiver


class Country(models.Model):

    iso = models.CharField('ISO', max_length=2, primary_key=True)
    name = models.CharField('Name', max_length=128)

    class Meta:
        verbose_name = 'Country'
        verbose_name_plural = 'Countries'
        ordering = ('name',)
        db_table = "country"

    def __str__(self):
        return self.name


class UserRole(models.Model):

    name = models.CharField(max_length=32)

    def __str__(self):
        return self.name


class UserProfile(models.Model):

    user = models.OneToOneField(auth.models.User, on_delete=models.CASCADE)

    current_role = models.ForeignKey(
        UserRole, related_name="current_role", null=True)
    roles = models.ManyToManyField(UserRole)

    home_country = models.ForeignKey(
        Country, related_name="home_country", null=True)
    countries = models.ManyToManyField(Country)

    @property
    def role(self):
        return self.current_role.name

    @property
    def country(self):
        if self.home_country is None:
            #@TODO  Please remove this when User management is added
            #      in the frontend.
            return "User without a country"
        return self.home_country.name

    def __str__(self):
        return self.user.username


@receiver(models.signals.post_save, sender=auth.models.User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(models.signals.post_save, sender=auth.models.User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()


class TaxonomyTagGroup(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return 'Tagging by ' + self.name


class TaxonomyTag(models.Model):
    name = models.CharField(max_length=255)
    group = models.ForeignKey(TaxonomyTagGroup, related_name='tags')

    def __str__(self):
        return "Tag " + self.name


class TaxonomyClassification(mptt.models.MPTTModel):
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
        return "Level {} classification: {}".format(
            self.get_classification_level(), self.name
        )


models.signals.pre_save.connect(
    TaxonomyClassification.pre_save_classification_code,
    sender=TaxonomyClassification
)


class Legislation(models.Model):

    title = models.CharField(max_length=256)
    abstract = models.CharField(max_length=1024)
    country = models.ForeignKey(Country)
    language = models.CharField(choices=constants.ALL_LANGUAGES,
                                default=constants.DEFAULT_LANGUAGE,
                                max_length=64)
    law_type = models.CharField(choices=constants.LEGISLATION_TYPE,
                                default=constants.LEGISLATION_TYPE_DEFAULT,
                                max_length=64)
    year = models.IntegerField(default=constants.LEGISLATION_DEFAULT_YEAR)
    year_amendment = models.IntegerField(
        default=constants.LEGISLATION_DEFAULT_YEAR,
        null=True
    )
    year_mention = models.CharField(max_length=1024, blank=True, null=True)
    geo_coverage = models.CharField(
        choices=constants.GEOGRAPHICAL_COVERAGE,
        default=constants.GEOGRAPHICAL_COVERAGE_DEFAULT,
        max_length=64,
        null=True
    )
    source = models.CharField(max_length=256, null=True)
    source_type = models.CharField(choices=constants.SOURCE_TYPE,
                                   default=constants.SOURCE_TYPE_DEFAULT,
                                   max_length=64, null=True)
    website = models.URLField(max_length=2000, null=True)

    pdf_file = models.FileField(null=True)
    pdf_file_name = models.CharField(null=True, max_length=256)

    tags = models.ManyToManyField(TaxonomyTag)
    classifications = models.ManyToManyField(TaxonomyClassification)

    # @TODO: Change the __str__ to something more appropriate
    def __str__(self):
        return "Legislation: " + ' | '.join([self.country.name, self.law_type])


class LegislationArticle(models.Model):

    text = models.CharField(max_length=65535)
    legislation = models.ForeignKey(Legislation, related_name="articles")
    tags = models.ManyToManyField(TaxonomyTag)
    classifications = models.ManyToManyField(TaxonomyClassification)
    legislation_page = models.IntegerField()
    code = models.CharField(max_length=64)

    # @TODO: Change the __str__ to something more appropriate
    def __str__(self):
        return "Article: %s" % str(self.legislation)


class LegislationPage(models.Model):

    page_text = models.CharField(max_length=65535)
    page_number = models.IntegerField()
    legislation = models.ForeignKey(Legislation, related_name="page")

    def __str__(self):
        return "Page %d of Legislation %s" % (self.page_number, str(self.legislation.title))
