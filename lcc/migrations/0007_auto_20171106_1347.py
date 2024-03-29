# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-11-06 15:13
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("lcc", "0006_auto_20171101_1507"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="countrymetadata",
            name="legal_system",
        ),
        migrations.AddField(
            model_name="countrymetadata",
            name="legal_system",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="lcc.LegalSystem",
            ),
        ),
        migrations.RemoveField(
            model_name="countrymetadata",
            name="region",
        ),
        migrations.AddField(
            model_name="countrymetadata",
            name="region",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.CASCADE, to="lcc.Region"
            ),
        ),
        migrations.RemoveField(
            model_name="countrymetadata",
            name="sub_region",
        ),
        migrations.AddField(
            model_name="countrymetadata",
            name="sub_region",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="lcc.SubRegion",
            ),
        ),
    ]
