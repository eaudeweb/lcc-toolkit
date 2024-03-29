# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-06-15 09:00
from __future__ import unicode_literals

from django.contrib.auth.management import create_permissions
from django.db import migrations


def update_group_permissions(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    content_manager, _ = Group.objects.get_or_create(name="Content manager")
    permissions = Permission.objects.filter(content_type__model="legislation")
    content_manager.permissions.add(*permissions)


class Migration(migrations.Migration):

    dependencies = [
        ("lcc", "0015_auto_20180606_0725"),
    ]

    operations = [
        migrations.RunPython(update_group_permissions),
    ]
