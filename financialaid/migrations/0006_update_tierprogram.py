# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-09-28 18:38
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('financialaid', '0005_switch_jsonfield'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tierprogram',
            name='tier',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tier_programs', to='financialaid.Tier'),
        ),
    ]