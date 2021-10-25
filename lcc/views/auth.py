import json

from http import HTTPStatus

from django.contrib.auth import (
    authenticate,
    login,
    logout,
    mixins,
    update_session_auth_hash,
)
from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import TemplateView, FormView

from lcc import constants


class Login(TemplateView):
    template_name = "auth/login.html"

    def post(self, request, *args, **kwargs):
        user = authenticate(
            request,
            username=request.POST[constants.POST_DATA_USERNAME_KEY],
            password=request.POST[constants.POST_DATA_PASSWORD_KEY],
        )
        if user:
            login(request, user)
            return HttpResponse(json.dumps({"msg": constants.AJAX_RETURN_SUCCESS}))
        else:
            return HttpResponse(
                json.dumps({"msg": constants.AJAX_RETURN_FAILURE}),
                status=HTTPStatus.UNAUTHORIZED,
            )


class Logout(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return HttpResponseRedirect(reverse("lcc:home_page"))


class ChangePasswordView(mixins.LoginRequiredMixin, FormView):
    template_name = "auth/change_password.html"
    form_class = PasswordChangeForm
    success_url = "/"
    permission_denied_redirect = reverse_lazy("auth:login")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        update_session_auth_hash(self.request, form.user)
        return super().form_valid(form)
