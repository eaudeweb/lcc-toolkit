# Generated by Django 3.1.13 on 2022-05-30 05:30

from django.db import migrations, models
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ('lcc', '0027_auto_20220518_1241'),
    ]

    operations = [
        migrations.CreateModel(
            name='StaticPage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', tinymce.models.HTMLField()),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('page', models.IntegerField(choices=[(0, 'About us'), (1, 'Footer'), (2, 'Homepage'), (3, 'Lessons learned')], default=1, help_text='Page location')),
            ],
            options={
                'verbose_name': 'Static page',
                'verbose_name_plural': 'Static pages',
                'ordering': ['page', 'last_modified'],
            },
        ),
    ]
