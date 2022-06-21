from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe
from lcc import models


User = get_user_model()

class LegislationSectionInline(admin.TabularInline):
    model = models.LegislationSection
    readonly_fields = ['pk', 'text', 'code', 'number', 'identifier']
    fields = readonly_fields

class LegislationAdmin(admin.ModelAdmin):
    list_display = (
        '__str__', 'title', 'pk', 'import_from_legispro', 'date_updated', 'date_created',
        'classifications_list', 'tags_list'
    )
    list_filter = ('import_from_legispro', 'law_type', 'country')
    search_fields = (
        'title', 'country__name',
        'classifications__name', 'tags__name'
    )
    actions = ['generate_pages']
    inlines = [LegislationSectionInline,]

    def classifications_list(self, obj):
        return "; ".join(obj.classifications.values_list("name", flat=True))

    def tags_list(self, obj):
        return "; ".join(obj.tags.values_list("name", flat=True))

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
            request,
            (
                "Pages were generated for {} laws, regenerated for {} and {} "
                "were skipped due to absent PDF."
            ).format(generated, regenerated, no_pdf),
        )

    generate_pages.short_description = "(Re)generate text pages from PDF"

    classifications_list.short_description = "Classifications"
    tags_list.short_description = "Cross cutting categories"


class ApprovedFilter(admin.SimpleListFilter):
    title = "Approved"
    parameter_name = "approved"

    def lookups(self, request, model_admin):
        return [
            (True, "Yes"),
            (False, "No"),
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

    get_approve_url.short_description = "Approve URL"

    def get_active(self, obj):
        return obj.is_active

    get_active.boolean = True
    get_active.short_description = "Approved"


class UserProfileInline(admin.StackedInline):
    model = models.UserProfile
    extra = 1
    max_num = 1
    min_num = 1


class UserAdmin(BaseUserAdmin):
    search_fields = ["username", "first_name", "last_name"]
    list_display = (
        "username",
        "first_name",
        "last_name",
        "email",
        "date_joined",
        "get_active",
        "get_approve_url",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "groups",
        ApprovedFilter,
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'password1', 'password2', 'first_name', 'last_name',
                'is_superuser', 'is_staff')}
        ),
    )
    inlines = [UserProfileInline]


@admin.register(models.UserProxy)
class UserProxyAdmin(BaseUserAdmin):
    list_display = ("username", "first_name", "last_name", "get_approve_url")
    list_display_links = None

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return self.model.objects.filter(is_active=False)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = [f.name for f in self.model._meta.fields]
        readonly_fields += ["groups", "user_permissions"]
        return readonly_fields


class LegislationSectionAdmin(admin.ModelAdmin):
    list_display = ("code", "code_order", "number", "identifier", "legispro_identifier", "legislation")
    search_fields = (
        'code',
    )
    list_filter = (
        'legislation',
    )
    def get_queryset(self, request):
        return self.model.objects.extra(
            select={
                "code_order_fix": "string_to_array(code_order, '.')::int[]",
            },
        ).order_by("code_order_fix")


class StaticPageAdmin(admin.ModelAdmin):
    list_display = ("__str__", "last_modified")

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj=obj, change=change, **kwargs)
        form.base_fields["text"].help_text = mark_safe("""
          <h4 style="color: black;">
            This is a WYSIWYG editor (short for "What You See Is What You Get" editor). You can use it to edit the text in a specific selected page.<br><br>

            If you click the last button on the editor toolbar (the button with a question mark), a helper modal will appear. There you can find the section "Handy shortcuts" and "Keyboard navigation" that might be helpful when you edit large text.<br><br>

            For this version, the file browsing is not available for adding images. But you can add any image with a valid, not restricted url.<br><br>

            How to add an image:<br>
            1. open in a new tab any image you want.<br>
            2. right click the image and select option "Copy image"<br>
            3. select the editor and paste it (ctrl + v or command + v for MacOS)<br><br>

            After the image was added you can:<br>
            1. edit its size by dragging the margins<br>
            2. right click the image and select the image option. This will open a modal where you can do multiple things<br>
            &nbsp  a. Change the url source of the image<br>
            &nbsp  b. Change the alternative description (what the browser will display in case the image can not be loaded)<br>
            &nbsp  c. Define a width and height for the image<br>
            3. right click the image and select the link option. With this option you can attach a link that you can access when you click the image (we have an example for this in the footer section)
          <h4>
        """)
        return form

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["page"]
        else:
            return []


# Register your models here.
admin.site.register(models.Legislation, LegislationAdmin)
admin.site.register(models.LegislationSection, LegislationSectionAdmin)
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
admin.site.register(models.LogicalCategory)
admin.site.register(models.StaticPage, StaticPageAdmin)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
