import re
import pdftotext

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from django.db.models import Q

from django import forms
from django.forms import ModelForm

from rolepermissions.roles import get_user_roles
from rolepermissions.roles import RolesManager

from lcc import roles
from lcc import models
from lcc.constants import LEGISLATION_YEAR_RANGE


class ArticleForm(ModelForm):
    class Meta:
        model = models.LegislationArticle
        fields = [
            'code', 'text', 'legislation', 'legislation_page', 'classifications', 'tags'
        ]


class LegislationForm(ModelForm):
    class Meta:
        model = models.Legislation
        fields = [
            'title', 'abstract', 'country', 'language', 'law_type', 'year',
            'year_amendment', 'year_mention', 'geo_coverage', 'source',
            'source_type', 'website', 'pdf_file', 'tags', 'classifications'
        ]

    def clean_year_mention(self):
        year_mention = self.cleaned_data['year_mention']
        if year_mention:
            years_in_year_mention = [
                int(year)
                for year in re.findall('\d\d\d\d', year_mention)
            ]

            if years_in_year_mention:
                if not any(year in LEGISLATION_YEAR_RANGE
                           for year in years_in_year_mention):
                    self.add_error('year_mention',
                                   "Please add a year in %d-%d range" % (
                                       LEGISLATION_YEAR_RANGE[0],
                                       LEGISLATION_YEAR_RANGE[-1]))
            else:
                self.add_error('year_mention', "'Additional date details' field needs "
                                               "a 4 digit year.")
        return year_mention

    def clean_website(self):
        website = self.cleaned_data['website']
        url = URLValidator()
        try:
            url(website)
        except ValidationError:
            self.add_error("website", "Please enter a valid website.")
        return website

    def clean_pdf_file(self):
        file = self.cleaned_data['pdf_file']
        try:
            pdftotext.PDF(file)
        except pdftotext.Error:
            self.add_error("pdf_file", "The .pdf file is corrupted. Please reupload it.")
        return file

    def save(self, commit=True):
        instance = super(LegislationForm, self).save(commit=False)
        instance.pdf_file_name = instance.pdf_file.name
        instance.save()
        return instance


class RegisterForm(ModelForm):

    email = forms.EmailField(label='Email address')
    role = forms.ChoiceField(
        label='Desired role',
        choices=map(lambda x: (x, x), filter(
            lambda n: n != roles.SiteAdministrator.get_name(),
            RolesManager.get_roles_names()
        ))
    )

    class Meta:
        model = models.UserProfile
        exclude = ['user', 'countries']
        labels = {
            'home_country': 'Country',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        widgets = (field.widget for field in self.fields.values())
        for widget in widgets:
            widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = self.cleaned_data['email']
        users_with_email = models.User.objects.filter(
            Q(email=email) | Q(username=email)
        )

        if users_with_email:
            raise ValidationError('That email address is already registered!')

        return email

    def save(self, commit=False):
        profile = super().save(commit=False)

        email = self.cleaned_data['email']
        role = RolesManager.retrieve_role(self.cleaned_data['role'])

        # create user
        user = models.User.objects.create_user(email, email=email)
        role.assign_role_to_user(user)
        user.is_active = False
        user.save()

        # assign to profile
        profile.user = user
        profile.save()

        return profile


class ApproveRegistration(ModelForm):
    role = forms.ChoiceField(
        label='Desired role',
        choices=map(
            lambda x: (x, x),
            RolesManager.get_roles_names()
        )
    )

    class Meta:
        model = models.UserProfile
        fields = []

    def save(self, notify):
        user = self.instance.user

        # remove any existing roles
        for role in get_user_roles(user):
            role.remove_role_from_user(user)

        to_assign = RolesManager.retrieve_role(self.cleaned_data['role'])
        to_assign.assign_role_to_user(user)

        user.is_active = True
        user.save()

        notify(user, to_assign.get_name())

    def delete(self, notify):
        email = self.instance.user.email
        self.instance.user.delete()
        notify(email)
