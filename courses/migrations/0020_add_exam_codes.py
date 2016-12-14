# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-14 17:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0019_courserun_default_ordering'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='exam_module',
            field=models.CharField(max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='program',
            name='exam_series_code',
            field=models.CharField(max_length=20, null=True),
        ),
    ]
