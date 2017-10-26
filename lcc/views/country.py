from django.views.generic import DetailView
from django.views.generic import UpdateView
from django.shortcuts import get_object_or_404

import lcc.models as models


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
        context = super().get_context_data(**kwargs)
        context['country'] = self.object.country
        context['meta'] = self.object
        return context
