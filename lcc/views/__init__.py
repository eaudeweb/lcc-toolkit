from .api import *
from .articles import *
from .auth import *
from .legislation import *
from .register import *


class Index(UserPatchMixin, views.View):
    def get(self, request):
        return HttpResponseRedirect(reverse('lcc:legislation:explorer'))


class LegalAssessment(mixins.LoginRequiredMixin, TemplateView):
    template_name = "assessment.html"
