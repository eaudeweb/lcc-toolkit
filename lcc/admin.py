from django.contrib import admin
from lcc import models


class LegislationAdmin(admin.ModelAdmin):
    list_display = (
        '__str__', 'title', 'pk',
        'classifications_list', 'tags_list'
    )
    list_filter = ('law_type', 'country')
    search_fields = (
        'title', 'country__name',
        'classifications__name', 'tags__name'
    )

    def classifications_list(self, obj):
        return '; '.join(
            obj.classifications.values_list('name', flat=True))

    def tags_list(self, obj):
        return '; '.join(
            obj.tags.values_list('name', flat=True))

    classifications_list.short_description = "Classifications"
    tags_list.short_description = "Cross cutting categories"


# Register your models here.
admin.site.register(models.Legislation, LegislationAdmin)
admin.site.register(models.LegislationArticle)
admin.site.register(models.LegislationPage)
admin.site.register(models.UserProfile)
admin.site.register(models.Country)
admin.site.register(models.AssessmentProfile)
admin.site.register(models.TaxonomyTagGroup)
admin.site.register(models.TaxonomyTag)
admin.site.register(models.TaxonomyClassification)

admin.site.register(models.Gap)
admin.site.register(models.Question)
admin.site.register(models.Assessment)
admin.site.register(models.Answer)
