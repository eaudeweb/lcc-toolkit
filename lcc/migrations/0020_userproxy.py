# -*- coding: utf-8 -*-
# Generated by Django 1.11.22 on 2019-07-30 12:51
from __future__ import unicode_literals

import django.contrib.auth.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0008_alter_user_username_max_length"),
        ("lcc", "0019_userprofile_approve_url"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserProxy",
            fields=[],
            options={
                "verbose_name": "Pending user approval",
                "verbose_name_plural": "Pending users approval",
                "proxy": True,
                "indexes": [],
            },
            bases=("auth.user",),
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
    ]
