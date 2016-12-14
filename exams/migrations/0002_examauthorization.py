# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-14 16:05
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0020_course_exam_series_code'),
        ('profiles', '0022_truncate_profile_image_uri'),
        ('exams', '0001_add_exam_profile'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExamAuthorization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('operation', models.CharField(choices=[('add', 'Add'), ('delete', 'Update'), ('update', 'Delete')], max_length=30)),
                ('status', models.CharField(choices=[('pending', 'Sync Pending'), ('in-progress', 'Sync in Progress'), ('failed', 'Sync Failed'), ('success', 'Sync Suceeded')], max_length=30)),
                ('date_first_eligible', models.DateTimeField()),
                ('date_last_eligible', models.DateTimeField()),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exam_authorizations', to='courses.Course')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exam_authorizations', to='profiles.Profile')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
