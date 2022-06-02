from django.conf import settings
from lcc.models import StaticPage


def sentry(request):
    sentry_id = ""
    if hasattr(request, "sentry"):
        sentry_id = request.sentry["id"]
    return {
        "sentry_id": sentry_id,
        "sentry_public_id": getattr(settings, "SENTRY_PUBLIC_DSN", ""),
    }


def ga_tracking_id(request):
    return {"ga_tracking_id": getattr(settings, "GA_TRACKING_ID", "")}


def footer_page(request):
    footer = StaticPage.objects.filter(page=StaticPage.FOOTER).first()
    return {"footer_page": footer}
