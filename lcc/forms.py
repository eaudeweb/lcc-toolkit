import re
import pdftotext

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.forms import ModelForm
from django.forms.utils import ErrorList

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
