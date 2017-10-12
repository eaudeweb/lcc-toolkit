from django.contrib import admin
from lcctoolkit.mainapp import models


# Register your models here.
admin.site.register(models.Legislation)
admin.site.register(models.LegislationArticle)
admin.site.register(models.LegislationPage)
admin.site.register(models.UserRole)
admin.site.register(models.UserProfile)
admin.site.register(models.Country)
admin.site.register(models.TaxonomyTagGroup)
admin.site.register(models.TaxonomyTag)
admin.site.register(models.TaxonomyClassification)

admin.site.register(models.Question)
admin.site.register(models.Assessment)
admin.site.register(models.Answer)
