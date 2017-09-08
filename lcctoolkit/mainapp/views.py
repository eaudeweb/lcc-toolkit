from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return HttpResponse("Hello world from main application of law climate change toolkit project!")
