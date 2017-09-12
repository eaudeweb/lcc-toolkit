import mptt.models
import lcctoolkit.mainapp as mainapp

from django.db import models
from django.contrib import auth


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
    
         
class UserProfile(auth.models.User):
    
    current_role = models.ForeignKey(UserRole, related_name="current_role")        
    roles = models.ManyToManyField(UserRole)
    
    home_country = models.ForeignKey(Country, related_name="home_country", null=True)
    countries = models.ManyToManyField(Country)
    
    @property
    def role(self):
        return self.current_role.name

    @property
    def country(self):
        return self.home_country.name


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

    class MPTTMeta:
        order_insertion_by = ['code']

    @classmethod
    def _pre_save_classification_code_on_create(cls, instance):
        """Logic executed before saving a new TaxonomyClassification instance.
        Set the next code for the classification.
        """
        instance.code = mainapp.utils.generate_code(cls, instance)

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
