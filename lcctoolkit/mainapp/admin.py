from django.contrib import admin
from lcctoolkit.mainapp import models


# Register your models here.
admin.site.register(models.TaxonomyTagGroup)
admin.site.register(models.TaxonomyTag)
admin.site.register(models.TaxonomyClassification)
