import json

import django.contrib.auth as auth
import django.shortcuts
import django.http
import django.views

import lcctoolkit.mainapp.constants as constants
import lcctoolkit.mainapp.models as models


class Index(django.views.View):

    template = "index.html"

    def get(self, request):
        return django.shortcuts.render(request, self.template)


class Login(django.views.View):

    template = "login.html"

    def get(self, request):
        return django.shortcuts.render(request, self.template)

    def post(self, request):
        user = auth.authenticate(
            request,
            username=request.POST[constants.POST_DATA_USERNAME_KEY],
            password=request.POST[constants.POST_DATA_PASSWORD_KEY]
        )
        if user:
            auth.login(request, user)
            return django.http.HttpResponse(
                json.dumps({'msg': constants.AJAX_RETURN_SUCCESS}))
        else:
            return django.http.HttpResponse(
                json.dumps({'msg': constants.AJAX_RETURN_FAILURE}))


class Logout(django.views.View):

    def get(self, request):
        auth.logout(request)
        return django.http.HttpResponseRedirect("/")


class LegislationMain(django.views.View):

    template = "legislation.html"

    def get(self, request):
        
        def update_law_object(law):
            law.all_tags=", ".join(law.tags.values_list('name', flat=True))
            return law

        return django.shortcuts.render(request, self.template, 
                {'laws': [update_law_object(law) 
                            for law in models.Legislation.objects.all()] })
