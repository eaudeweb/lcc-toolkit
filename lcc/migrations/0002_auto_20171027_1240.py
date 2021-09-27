# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-27 12:40
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("lcc", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Gap",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("on", models.BooleanField()),
                (
                    "classifications",
                    models.ManyToManyField(blank=True, to="lcc.TaxonomyClassification"),
                ),
                ("tags", models.ManyToManyField(blank=True, to="lcc.TaxonomyTag")),
            ],
        ),
        migrations.RemoveField(
            model_name="question",
            name="gap_on",
        ),
        migrations.RemoveField(
            model_name="question",
            name="tags",
        ),
        migrations.AlterField(
            model_name="question",
            name="classification",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="lcc.TaxonomyClassification",
            ),
        ),
        migrations.AddField(
            model_name="question",
            name="gaps",
            field=models.ManyToManyField(blank=True, to="lcc.Gap"),
        ),
    ]
