from django.template import loader, TemplateDoesNotExist
from django.http import HttpResponse, HttpResponseServerError

from lcctoolkit.context_processors import sentry


def handler500(request, template_name='errors/500.html'):
    try:
        template = loader.get_template(template_name)
    except TemplateDoesNotExist:
        return HttpResponseServerError('<h1>Server Error (500)</h1>',
                                            content_type='text/html')

    return HttpResponseServerError(template.render(context=sentry(request)))


def crashme(request):
    if request.user.is_superuser:
        raise RuntimeError("Crashing as requested")
    else:
        return HttpResponse("Must be administrator")