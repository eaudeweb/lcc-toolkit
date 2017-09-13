import django.contrib.auth as auth
import django.shortcuts
import django.http

import json


def index(request):
    return django.shortcuts.render(request, "index.html", {})


def login(request):
    if request.method == "GET":
        return django.shortcuts.render(request, "login.html", {})
    elif request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = auth.authenticate(request, username=username, password=password)
        if user:
            auth.login(request, user)
            return django.http.HttpResponse(json.dumps({'msg': 'success'}))
        else:
            return django.http.HttpResponse(json.dumps({'msg': 'failure'}))

def logout(request):
        auth.logout(request)
        return django.http.HttpResponseRedirect("/")