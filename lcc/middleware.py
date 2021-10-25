""" Middleware
https://docs.djangoproject.com/en/1.11/topics/http/middleware/#writing-your-own-middleware
"""


def user_profile(get_response):
    """Add user_profile on request."""

    def middleware(request):
        request.user_profile = (
            getattr(request.user, "userprofile", None)
            if request.user.is_authenticated
            else None
        )
        response = get_response(request)
        return response

    return middleware
