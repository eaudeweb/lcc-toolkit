# Generated by Django 3.1.13 on 2021-09-16 11:27

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
        ("lcc", "0021_auto_20200828_0908"),
    ]

    operations = [
        migrations.AlterField(
            model_name="legislation",
            name="year",
            field=models.IntegerField(default=2021),
        ),
        migrations.AlterField(
            model_name="legislationpage",
            name="page_text",
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name="question",
            name="level",
            field=models.PositiveIntegerField(editable=False),
        ),
        migrations.AlterField(
            model_name="question",
            name="lft",
            field=models.PositiveIntegerField(editable=False),
        ),
        migrations.AlterField(
            model_name="question",
            name="rght",
            field=models.PositiveIntegerField(editable=False),
        ),
        migrations.AlterField(
            model_name="taxonomyclassification",
            name="level",
            field=models.PositiveIntegerField(editable=False),
        ),
        migrations.AlterField(
            model_name="taxonomyclassification",
            name="lft",
            field=models.PositiveIntegerField(editable=False),
        ),
        migrations.AlterField(
            model_name="taxonomyclassification",
            name="rght",
            field=models.PositiveIntegerField(editable=False),
        ),
        migrations.CreateModel(
            name="LegislationSection",
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
                (
                    "_classification_ids",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.IntegerField(),
                        blank=True,
                        default=list,
                        size=None,
                    ),
                ),
                (
                    "_tag_ids",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.IntegerField(),
                        blank=True,
                        default=list,
                        size=None,
                    ),
                ),
                ("text", models.TextField()),
                ("legislation_page", models.IntegerField(blank=True, null=True)),
                ("number", models.IntegerField(blank=True, null=True)),
                (
                    "identifier",
                    models.IntegerField(blank=True, default=None, null=True),
                ),
                (
                    "legispro_identifier",
                    models.CharField(blank=True, max_length=256, null=True),
                ),
                ("code", models.CharField(blank=True, max_length=256)),
                ("lft", models.PositiveIntegerField(editable=False)),
                ("rght", models.PositiveIntegerField(editable=False)),
                ("tree_id", models.PositiveIntegerField(db_index=True, editable=False)),
                ("level", models.PositiveIntegerField(editable=False)),
                (
                    "classifications",
                    models.ManyToManyField(blank=True, to="lcc.TaxonomyClassification"),
                ),
                (
                    "legislation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sections",
                        to="lcc.legislation",
                    ),
                ),
                (
                    "parent",
                    mptt.fields.TreeForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="children",
                        to="lcc.legislationsection",
                    ),
                ),
                ("tags", models.ManyToManyField(blank=True, to="lcc.TaxonomyTag")),
            ],
            options={
                "ordering": ["code"],
            },
        ),
    ]
