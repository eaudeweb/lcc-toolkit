from .api import *
from .articles import *
from .auth import *
from .legislation import *


class Index(UserPatchMixin, views.View):
    def get(self, request):
        return HttpResponseRedirect(reverse('lcc:legislation:explorer'))


class LegalAssessment(mixins.LoginRequiredMixin, views.View):
    login_url = constants.LOGIN_URL
    template = "assessmetn.html"

    def get(self, request):
        return render(request, self.template)
