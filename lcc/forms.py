import re
import pdftotext

import operator
from itertools import chain

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.contrib.auth.forms import PasswordResetForm
from django.forms import ModelForm
from django.db.models import Q

from lcc import models
from lcc import roles
from lcc.constants import LEGISLATION_YEAR_RANGE

from rolepermissions.roles import get_user_roles
from rolepermissions.roles import RolesManager


class ArticleForm(ModelForm):
    class Meta:
        model = models.LegislationArticle
        fields = [
            'code', 'text', 'legislation', 'legislation_page',
            'classifications', 'tags'
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
        if not year_mention:
            return

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
                self.add_error(
                    'year_mention',
                    "'Additional date details' field needs a 4 digit year."
                )
        return year_mention

    def clean_website(self):
        website = self.cleaned_data['website']
        if not website:
            return

        url = URLValidator()
        try:
            url(website)
        except ValidationError:
            self.add_error("website", "Please enter a valid website.")
        return website

    def clean_pdf_file(self):
        if self.instance:
            if self.instance.import_from_legispro:
                return None
        file = self.cleaned_data['pdf_file']
        try:
            pdftotext.PDF(file)
        except pdftotext.Error:
            self.add_error(
                "pdf_file", "The .pdf file is corrupted. Please reupload it.")
        return file

    def save(self, commit=True):
        instance = super(LegislationForm, self).save(commit=False)
        instance.pdf_file_name = instance.pdf_file.name
        instance.save()
        instance.classifications = self.cleaned_data['classifications']
        instance.tags = self.cleaned_data['tags']
        instance.save()
        return instance


class RegisterForm(ModelForm):

    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField(label='Email address')
    role = forms.ChoiceField(
        label='Desired role',
        choices=map(lambda x: (x, x), filter(
            lambda n: n != roles.SiteAdministrator.get_name(),
            RolesManager.get_roles_names()
        ))
    )
    affiliation = forms.CharField(max_length=255, required=True)

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

        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']
        email = self.cleaned_data['email']
        role = RolesManager.retrieve_role(self.cleaned_data['role'])

        # create user
        user = models.User.objects.create_user(
            email,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
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


class PasswordResetNoUserForm(PasswordResetForm):
    """
       This subclass doesn't validate the form
       if there is no user with the e-mail provided.
    """
    def clean(self):
        context = super(PasswordResetForm, self).clean()
        try:
            models.User.objects.get(email=context['email'])
        except models.User.DoesNotExist:
            raise ValidationError("There is no user with this e-mail.")
        return context

class CountryBase(ModelForm):
    """ Used on view. """

    class Meta:
        model = models.AssessmentProfile
        exclude = ['user', 'country']

    def _filter_on_type(self, type_name, cmp):
        return (
            self[name] for name, field in self.fields.items()
            if cmp(field.widget.input_type, type_name)
        )

    def checkboxes(self):
        return self._filter_on_type('checkbox', operator.eq)

    def multiple(self):
        return self._filter_on_type('select', operator.eq)

    def others(self):
        return (
            field for field in (self[name] for name in self.fields)
            if field not in chain(self.checkboxes(), self.multiple())
        )


class CustomiseCountry(CountryBase):
    """ Used on edit. """
    def others(self):
        return self._filter_on_type('checkbox', operator.ne)

    def delete(self):
        self.instance.delete()
