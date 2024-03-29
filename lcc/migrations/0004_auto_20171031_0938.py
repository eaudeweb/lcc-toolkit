# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-31 09:38
from __future__ import unicode_literals

import django.contrib.postgres.fields
import django.contrib.postgres.indexes
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("lcc", "0003_auto_20171028_1425"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="question",
            name="gaps",
        ),
        migrations.AddField(
            model_name="gap",
            name="_classification_ids",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.IntegerField(), default=list, size=None
            ),
        ),
        migrations.AddField(
            model_name="gap",
            name="_tag_ids",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.IntegerField(), default=list, size=None
            ),
        ),
        migrations.AddField(
            model_name="gap",
            name="question",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="gaps",
                to="lcc.Question",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="legislation",
            name="_classification_ids",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.IntegerField(), default=list, size=None
            ),
        ),
        migrations.AddField(
            model_name="legislation",
            name="_tag_ids",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.IntegerField(), default=list, size=None
            ),
        ),
        migrations.AddField(
            model_name="legislationarticle",
            name="_classification_ids",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.IntegerField(), default=list, size=None
            ),
        ),
        migrations.AddField(
            model_name="legislationarticle",
            name="_tag_ids",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.IntegerField(), default=list, size=None
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
                default=("official", "Official"),
                max_length=64,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="legislationarticle",
            name="classifications",
            field=models.ManyToManyField(blank=True, to="lcc.TaxonomyClassification"),
        ),
        migrations.AlterUniqueTogether(
            name="gap",
            unique_together=set([("on", "question")]),
        ),
        migrations.AddIndex(
            model_name="gap",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["_classification_ids"], name="lcc_gap__classi_5bb05d_gin"
            ),
        ),
        migrations.AddIndex(
            model_name="gap",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["_tag_ids"], name="lcc_gap__tag_id_7f7066_gin"
            ),
        ),
        migrations.AddIndex(
            model_name="legislation",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["_classification_ids"], name="lcc_legisla__classi_06880e_gin"
            ),
        ),
        migrations.AddIndex(
            model_name="legislation",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["_tag_ids"], name="lcc_legisla__tag_id_44bd64_gin"
            ),
        ),
        migrations.AddIndex(
            model_name="legislationarticle",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["_classification_ids"], name="lcc_legisla__classi_4783e4_gin"
            ),
        ),
        migrations.AddIndex(
            model_name="legislationarticle",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["_tag_ids"], name="lcc_legisla__tag_id_fbb519_gin"
            ),
        ),
    ]
