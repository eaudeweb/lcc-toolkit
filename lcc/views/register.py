from functools import partial

from django.urls import reverse_lazy
from django.db import transaction
from django.db.models import Q

import django.contrib.auth as auth

from django.contrib.auth.models import User
from django.core.mail import send_mail

from django.template.loader import get_template
import django.shortcuts
from django.contrib.sites.shortcuts import get_current_site
import django.http
import django.views as views
from django.views.generic import CreateView
from django.utils.http import urlsafe_base64_encode
from django.utils.http import urlsafe_base64_decode

from django.utils.encoding import force_bytes
from django.utils.encoding import force_text

from rolepermissions.roles import RolesManager
from rolepermissions.roles import get_user_roles
from rolepermissions.mixins import HasRoleMixin

from lcc import roles
from lcc import models
from lcc import forms
from django.conf import settings


def _site_url(request):
    return '{protocol}://{domain}'.format(
        protocol=request._get_scheme(),
        domain=get_current_site(request),
    )


class PasswordResetConfirm(auth.views.PasswordResetConfirmView):
    success_url = reverse_lazy('password_reset_complete')
    template_name = "password_reset_confirm.html"


class PasswordResetComplete(auth.views.PasswordResetCompleteView):
    template_name = "password_reset_complete.html"


class Register(CreateView):
    """ Registration form.
    """

    template_name = "registration/register.html"

    form_class = forms.RegisterForm

    @transaction.atomic
    def form_valid(self, form):
        profile = form.save()
        self._send_admin_mails(profile.user)
        return django.shortcuts.render(
            self.request, self.template_name, dict(success=True))

    def _send_admin_mails(self, user):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        admin_emails = (
            User.objects
            .filter(is_staff=True)
            .values_list('email', flat=True)
        )
        template = get_template('mail/new_registration.html')
        body = template.render(dict(
            site_url=_site_url(self.request),
            uid=uid,
        ))
        subject = 'New user registration'
        send_mail(
            subject,
            body,
            settings.EMAIL_FROM,
            admin_emails,
            html_message=body,
            fail_silently=False
        )


class ApproveRegistration(HasRoleMixin, views.View):

    allowed_roles = [roles.SiteAdministrator]

    template = "approve_registration.html"

    @staticmethod
    def _get_profile(user_id, **override):
        profile = models.UserProfile.objects.get(user__pk=user_id)

        # Get requested role. This will break when dealing with a
        # registered user that has multiple roles assigned, before
        # activation, as a result of admin intervention.
        user_roles = get_user_roles(profile.user)
        role = user_roles[0].role_name if user_roles else ''

        return dict(
            user=profile.user,
            role=override.get('role', None) or role,
            email=profile.user.email,
            affiliation=profile.affiliation,
            position=profile.position,
            country=profile.home_country,
        )

    def get(self, request, uidb64):
        uid = force_text(urlsafe_base64_decode(uidb64))
        context = dict(
            profile=self._get_profile(uid),
            roles=RolesManager.get_roles_names(),
        )
        return django.shortcuts.render(request, self.template, context)

    @staticmethod
    def _send_mail(subject, body, recipients):
        send_mail(
            subject,
            body,
            settings.EMAIL_FROM,
            recipients,
            html_message=body,
            fail_silently=False)

    def _notify_denied(self, profile):
        template = get_template('mail/registration_denied.html')
        self._send_mail(
            'Registration denied!',
            template.render(dict(profile=profile)),
            [profile['email']]
        )

    def _notify_approved(self, profile):
        template = get_template('mail/registration_approved.html')
        token = auth.tokens.default_token_generator.make_token(profile['user'])
        uid = urlsafe_base64_encode(force_bytes(profile['user'].pk))
        self._send_mail(
            'Registration approved!',
            template.render(dict(
                profile=profile,
                token=token,
                uid=uid,
                site_url=_site_url(self.request),
            )),
            [profile['email']]
        )

    def _deny(self, profile):
        profile['user'].delete()
        self._notify_denied(profile)

    def _approve(self, profile):
        for role in map(RolesManager.retrieve_role, RolesManager()):
            role.remove_role_from_user(profile['user'])

        to_assign = RolesManager.retrieve_role(profile['role'])
        to_assign.assign_role_to_user(profile['user'])

        profile['user'].is_active = True
        profile['user'].save()

        self._notify_approved(profile)

    def _approve_or_deny(self, profile, approved, denied):
        """ Returns context for form confirmation message. """
        (self._approve if approved else self._deny if denied
         else lambda _: None)(profile)

        return dict(approved=approved, denied=denied, profile=profile)

    @transaction.atomic
    def post(self, request, uidb64):
        uid = force_text(urlsafe_base64_decode(uidb64))
        profile = self._get_profile(uid, role=request.POST.get('role'))
        context = self._approve_or_deny(profile, *map(
            request.POST.get, ('approve', 'deny')))

        return django.shortcuts.render(request, self.template, context)
