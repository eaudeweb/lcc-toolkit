from copy import deepcopy

from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView, UpdateView, DeleteView

import lcc.models as models
import lcc.forms as forms


class Metadata:
    labels = dict(
        population_range='Population range',
        hdi2015_range='HDI Range',
        gdp_capita_range='GDP Range',
        ghg_no_lucf_range=(
            'Total GHG Emissions excluding LUCF MtCO2e 2014 ranges'
        ),
        ghg_lucf_range='Total GHG Emissions including LUCF MtCO2e 2014 ranges'
    )

    def __init__(self, original, customised):
        self.form = forms.CountryMetadata()
        self.original = original
        self.customised = customised

    def __iter__(self):
        for name in self.form.fields:
            yield getattr(self, name)
            range = f'{name}_range'
            if hasattr(self.original, range):
                yield getattr(self, range)

    @staticmethod
    def _get_value(target, name):
        value = getattr(target, name)
        return (
            [v.name for v in value.all()]
            if hasattr(value, 'all')
            else value
        )

    def _get_label(self, name):
        return (
            self.labels[name]
            if name in self.labels
            else self.form[name].label
        )

    def _get_type(self, name):
        field = self.form.fields.get(name, None)

        if not field:
            return None

        if getattr(field.widget, 'allow_multiple_selected', None):
            return 'multiple'

        return field.widget.input_type

    def __getattr__(self, name):
        val_orig = self._get_value(self.original, name)
        val_custom = (
            self._get_value(self.customised, name)
            if self.is_customised()
            else val_orig
        )

        return dict(
            value=val_custom,
            orig=val_orig,
            label=self._get_label(name),
            type=self._get_type(name),
            modified=val_custom != val_orig
        )

    def is_customised(self):
        return self.customised is not None


class Details(DetailView):
    template_name = 'country/view.html'
    model = models.CountryMetadata
    pk_url_kwarg = 'iso'

    def get_object(self):
        iso = self.kwargs.get(self.pk_url_kwarg)
        return get_object_or_404(
            self.model,
            country__iso=iso,
            user=None
        )

    def get_context_data(self, **kwargs):
        countries = models.Country.objects.all()
        context = super().get_context_data(**kwargs)
        context['countries'] = countries
        context['country'] = self.object.country
        try:
            metadata_user = self.model.objects.get(
                country__iso=self.object.country.iso,
                user=self.request.user_profile
            )
        except self.model.DoesNotExist:
            metadata_user = None

        context['meta'] = Metadata(self.object, metadata_user)

        return context


def _get_user_metadata(model, iso, user_profile):
    try:
        meta = model.objects.get(country__iso=iso, user=user_profile)
    except model.DoesNotExist:
        original = model.objects.get(country__iso=iso, user=None)
        meta = original.clone_to_profile(user_profile)
    return meta


class Customise(UpdateView):
    template_name = 'country/customise.html'
    model = models.CountryMetadata
    form_class = forms.CustomiseCountry
    pk_url_kwarg = 'iso'

    @transaction.atomic
    def get_object(self):
        iso = self.kwargs.get(self.pk_url_kwarg)
        return _get_user_metadata(self.model, iso, self.request.user_profile)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['country'] = self.object.country
        context['meta'] = self.object
        return context

    @transaction.atomic
    def form_valid(self, form):
        if self.request.POST.get('save'):
            form.save()

        elif self.request.POST.get('discard'):
            form.delete()

        return HttpResponseRedirect(self.get_success_url())


class DeleteCustomisedProfile(DeleteView):
    model = models.CountryMetadata
    pk_url_kwarg = 'iso'

    def get_success_url(self, **kwargs):
        iso = self.kwargs.get(self.pk_url_kwarg)
        return reverse('lcc:country:view', kwargs={
            'iso': iso
        })

    def get_object(self):
        iso = self.kwargs.get(self.pk_url_kwarg)
        return models.CountryMetadata.objects.get(
            user=self.request.user_profile,
            country__iso=iso
        )

    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)
