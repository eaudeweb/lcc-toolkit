# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-04-15 08:59
from __future__ import unicode_literals

from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ("lcc", "0017_add_taxonomy_details"),
    ]

    operations = [
        migrations.AddField(
            model_name="country",
            name="iso_code",
            field=models.CharField(
                default="", max_length=2, verbose_name="Iso alpha 2"
            ),
        ),
        migrations.AlterField(
            model_name="legislation",
            name="year",
            field=models.IntegerField(default=2019),
        ),
        migrations.AddField(
            model_name="legislation",
            name="date_created",
            field=models.DateTimeField(auto_now_add=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="legislation",
            name="date_updated",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="legislation",
            name="import_from_legispro",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="legislation",
            name="legispro_article",
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
        migrations.AddField(
            model_name="legislationarticle",
            name="legispro_identifier",
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name="legislationarticle",
            name="legislation_page",
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name="taxonomyclassification",
            name="legispro_code",
            field=models.CharField(blank=True, max_length=16),
        ),
        migrations.AlterField(
            model_name="legislation",
            name="geo_coverage",
            field=models.CharField(
                choices=[
                    ("nat", "National"),
                    ("int-reg", "International/regional"),
                    ("st-pr", "State/province"),
                    ("city-mun", "City/municipality"),
                    ("oth", "Other"),
                ],
                default="National",
                max_length=64,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="legislation",
            name="language",
            field=models.CharField(
                choices=[
                    ("en", "English"),
                    ("ar", "Arabic"),
                    ("zh", "Chinese"),
                    ("fr", "French"),
                    ("ru", "Russian"),
                    ("es-es", "Spanish"),
                    ("oth", "Other"),
                ],
                default="English",
                max_length=64,
            ),
        ),
        migrations.AlterField(
            model_name="legislation",
            name="law_type",
            field=models.CharField(
                choices=[
                    ("Law", "Law"),
                    ("Constitution", "Constitution"),
                    ("Regulation", "Regulation"),
                    ("oth", "Other"),
                ],
                default="Law",
                max_length=64,
            ),
        ),
        migrations.AlterField(
            model_name="legislation",
            name="source_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("official", "Official"),
                    ("unofficial", "Unofficial"),
                    ("", "----"),
                ],
                default="Official",
                max_length=64,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="legislationarticle",
            name="legislation_page",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="legislation",
            name="pdf_file",
            field=models.FileField(blank=True, null=True, upload_to=""),
        ),
    ]
