from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe
from lcc import models


User = get_user_model()


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
    actions = ['generate_pages']

    def classifications_list(self, obj):
        return '; '.join(
            obj.classifications.values_list('name', flat=True))

    def tags_list(self, obj):
        return '; '.join(
            obj.tags.values_list('name', flat=True))

    def generate_pages(self, request, queryset):
        generated = 0
        regenerated = 0
        no_pdf = 0
        for law in queryset:
            old_pages = law.pages.all()
            old_pages.delete()

            if not law.pdf_file:
                no_pdf += 1
                continue

            law.save_pdf_pages()

            if old_pages:
                regenerated += 1
            else:
                generated += 1
        self.message_user(
            request, (
                "Pages were generated for {} laws, regenerated for {} and {} "
                "were skipped due to absent PDF."
            ).format(generated, regenerated, no_pdf)
        )
    generate_pages.short_description = "(Re)generate text pages from PDF"

    classifications_list.short_description = "Classifications"
    tags_list.short_description = "Cross cutting categories"


class ApprovedFilter(admin.SimpleListFilter):
    title = 'Approved'
    parameter_name = 'approved'

    def lookups(self, request, model_admin):
        return [
            (True, 'Yes'),
            (False, 'No'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(is_active=self.value())
        return queryset


class BaseUserAdmin(UserAdmin):
    def get_approve_url(self, obj):
        url = obj.userprofile.approve_url
        link = ""
        if url and not obj.is_active:
            link = '<a href="%s">%s</a>' % (url, url)
        return mark_safe(link)
    get_approve_url.short_description = 'Approve URL'

    def get_active(self, obj):
        return obj.is_active
    get_active.boolean =  True
    get_active.short_description = 'Approved'



class UserAdmin(BaseUserAdmin):
    search_fields = ["username", "first_name", "last_name"]
    list_display = (
        "username", "first_name", "last_name", "email", "get_active",
        "get_approve_url"
    )
    list_filter = (
        "is_staff", "is_superuser", "groups", ApprovedFilter,
    )


@admin.register(models.UserProxy)
class UserProxyAdmin(BaseUserAdmin):
    list_display = (
        "username", "first_name", "last_name", "get_approve_url"
    )
    list_display_links = None

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return self.model.objects.filter(is_active=False)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = [f.name for f in self.model._meta.fields]
        readonly_fields += ['groups', 'user_permissions']
        return readonly_fields


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

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
