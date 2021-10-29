from django.urls import reverse_lazy
from django.db import transaction

import django.contrib.auth as auth

from django.contrib.auth.models import User
from django.core.mail import send_mail

from django.template.loader import get_template

from django.shortcuts import render
from django.shortcuts import get_object_or_404

from django.contrib.sites.shortcuts import get_current_site

from django.views.generic import CreateView
from django.views.generic import UpdateView

from django.utils.http import urlsafe_base64_encode
from django.utils.http import urlsafe_base64_decode

from django.utils.encoding import force_bytes
from django.utils.encoding import force_text

from django.urls import reverse

from rolepermissions.roles import get_user_roles
from rolepermissions.roles import RolesManager
from rolepermissions.mixins import HasRoleMixin

from lcc import roles
from lcc import models
from lcc import forms
from django.conf import settings


def _site_url(request):
    return settings.DOMAIN


def _send_mail(subject, body, recipients):
    send_mail(
        subject,
        body,
        settings.EMAIL_FROM,
        recipients,
        html_message=body,
        fail_silently=False,
    )


class PasswordResetView(auth.views.PasswordResetView):
    from_email = settings.EMAIL_FROM
    template_name = "register/password_reset_form.html"
    email_template_name = "mail/password_reset_email.html"
    html_email_template_name = "mail/password_reset_email.html"
    subject_template_name = "mail/password_reset_subject.txt"
    success_url = reverse_lazy("lcc:home_page")
    form_class = forms.PasswordResetNoUserForm


class PasswordResetConfirm(auth.views.PasswordResetConfirmView):
    success_url = reverse_lazy("lcc:auth:password_reset_complete")
    template_name = "register/password_reset_confirm.html"


class PasswordResetComplete(auth.views.PasswordResetCompleteView):
    template_name = "register/password_reset_complete.html"


class Register(CreateView):
    """Registration form."""

    template_name = "register/register.html"

    form_class = forms.RegisterForm

    @transaction.atomic
    def form_valid(self, form):
        profile = form.save()

        # bypass approval process for now
        self._notify_approved(profile)

        self._send_admin_mails(profile)
        return render(self.request, self.template_name, dict(success=True))

    def _send_admin_mails(self, profile):
        profile_id = urlsafe_base64_encode(force_bytes(profile.pk))
        approve_url = _site_url(self.request) + reverse(
            "lcc:auth:approve", kwargs={"profile_id_b64": profile_id}
        )
        profile.approve_url = approve_url
        profile.save()
        admin_emails = User.objects.filter(is_staff=True).values_list(
            "email", flat=True
        )
        template = get_template('mail/new_registration_approved.html')
        body = template.render(
            dict(
                site_url=_site_url(self.request),
                profile_id=profile_id,
            )
        )

        subject = "New user registration in the Law and Climate Change Toolkit"
        _send_mail(subject, body, admin_emails)

    def _notify_approved(self, profile):
        user = profile.user
        user.is_active = True
        user.save()
        template = get_template('mail/registration_approved.html')
        token = auth.tokens.default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        role_name = profile.roles[0].get_name()

        if role_name == 'Other':
            role_name = profile.other_role

        _send_mail(
            'Climate Law Toolkit Registration',
            template.render(dict(
                user=user,
                role_name=role_name,
                token=token,
                uid=uid,
                site_url=_site_url(self.request)
            )),
            [user.email]
        )


class ApproveRegistration(HasRoleMixin, UpdateView):

    allowed_roles = [roles.SiteAdministrator]

    template_name = "register/approve_registration.html"

    model = models.UserProfile

    form_class = forms.ApproveRegistration

    pk_url_kwarg = "profile_id_b64"

    def get_initial(self):
        # Get requested role. This will break when dealing with a
        # registered user that has multiple roles assigned, before
        # activation, as a result of admin intervention.
        user_roles = get_user_roles(self.object.user)
        role = user_roles[0].role_name if user_roles else ""
        return dict(role=role)

    def get_object(self):
        pk_base64 = self.kwargs.get(self.pk_url_kwarg)
        pk = force_text(urlsafe_base64_decode(pk_base64))
        return get_object_or_404(self.model, pk=pk)

    def get_role(self):
        user_roles = get_user_roles(self.object.user)
        return user_roles[0].role_name if user_roles else ''

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.object
        context['role'] = self.get_role()
        return context

    @transaction.atomic
    def form_valid(self, form):
        context = dict()
        if self.request.POST.get("approve"):
            form.save(self._notify_approved)
            context = dict(approved=True)

        elif self.request.POST.get("deny"):
            form.delete(self._notify_denied)
            context = dict(denied=True)

        return render(self.request, self.template_name, context)

    def _notify_denied(self, email):
        template = get_template("mail/registration_denied.html")
        _send_mail("Registration denied!", template.render(), [email])

    def _notify_approved(self, user, role_name):
        template = get_template("mail/registration_approved.html")
        token = auth.tokens.default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        _send_mail(
            "Climate Law Toolkit Registration",
            template.render(
                dict(
                    user=user,
                    role_name=role_name,
                    token=token,
                    uid=uid,
                    site_url=_site_url(self.request),
                )
            ),
            [user.email],
        )
