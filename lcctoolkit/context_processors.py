from django.conf import settings


def sentry(request):
    sentry_id = ''
    if hasattr(request, 'sentry'):
        sentry_id = request.sentry['id']
    return {
        'sentry_id': sentry_id,
        'sentry_public_id': getattr(settings, 'SENTRY_PUBLIC_DSN', ''),
    }