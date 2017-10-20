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
from django.utils.http import urlsafe_base64_encode
from django.utils.http import urlsafe_base64_decode

from django.utils.encoding import force_bytes
from django.utils.encoding import force_text

from rolepermissions.roles import RolesManager
from rolepermissions.roles import get_user_roles
from rolepermissions.mixins import HasRoleMixin

from lcc import roles
from lcc import models
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


class Register(views.View):
    """ Registration form.
    """

    template = "register.html"

    @staticmethod
    def _context(**kwargs):
        def _skip_admin(name):
            return name != roles.SiteAdministrator.get_name()

        default = (
            ('countries', models.Country.objects.order_by('name')),
            ('roles', filter(_skip_admin, RolesManager.get_roles_names()))
        )

        return dict(default + tuple(kwargs.items()))

    def _validate_post(self, request):
        def _validate(request, field, msg, must_pass=lambda val: val):
            """ accepts an "extra" validator function """
            valid = must_pass(request.POST.get(field))
            return (field, msg) if not valid else None

        validate = partial(_validate, request)
        validate_email = (
            validate('email', 'Email is required!') or
            validate(
                'email', 'Email already registered!',
                must_pass=lambda email: len(
                    User.objects.filter(
                        Q(email=email) | Q(username=email))) == 0
            )
        )
        validate_country = validate('country', 'Country is required!')
        validate_role = validate(
            'role', 'You must choose a role!',
            must_pass=RolesManager.retrieve_role
        )

        return dict(
            filter(bool, (validate_email, validate_country, validate_role)))

    def get(self, request):
        context = self._context()
        return django.shortcuts.render(request, self.template, context)

    def _respond_with_errors(self, errors, request):
        # preserve input data
        default = {
            fname: request.POST.get(fname) for
            fname in ('email', 'country', 'role')
        }

        return self._context(errors=errors, default=default)

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

    def _respond_with_success(self, request):
        role = RolesManager.retrieve_role(request.POST.get('role'))

        # add user, mark as inactive
        email = request.POST.get('email')
        user = User.objects.create_user(email, email=email)
        user.is_active = False
        user.save()

        # set country
        country = request.POST.get('country')
        user.userprofile.home_country = models.Country.objects.get(iso=country)
        user.userprofile.affiliation = request.POST.get('affiliation')
        user.userprofile.position = request.POST.get('position')
        user.userprofile.save()

        # grant role
        role.assign_role_to_user(user)

        # notify admins
        self._send_admin_mails(user)

        return self._context(success=True)

    @transaction.atomic
    def post(self, request):
        errors = self._validate_post(request)
        context = (
            self._respond_with_errors(errors, request) if errors
            else self._respond_with_success(request)
        )
        return django.shortcuts.render(request, self.template, context)


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
