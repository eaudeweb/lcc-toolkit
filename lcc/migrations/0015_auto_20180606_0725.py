# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-06-06 07:25
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lcc', '0014_auto_20180524_0800'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='home_country',
            field=models.ForeignKey(default='GBR', on_delete=django.db.models.deletion.CASCADE, related_name='home_country', to='lcc.Country'),
            preserve_default=False,
        ),
    ]
