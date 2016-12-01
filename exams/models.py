"""
Models for exams
"""
from django.db import models
from django.db.models import Model

from profiles.models import Profile


class ExamProfile(Model):
    """
    Profile model to track syncing this data to the remote
    """
    PROFILE_INVALID = 'INV'
    PROFILE_PENDING = 'PND'
    PROFILE_IN_PROGRESS = 'INP'
    PROFILE_FAILED = 'FL'
    PROFILE_SUCCESS = 'FL'

    PROFILE_STATUS_CHOICES = (
        (PROFILE_PENDING, 'Sync Pending'),
        (PROFILE_IN_PROGRESS, 'Sync in Progress'),
        (PROFILE_FAILED, 'Sync Failed'),
        (PROFILE_SUCCESS, 'Sync Suceeded'),
    )

    profile = models.OneToOneField(Profile, related_name='exam_profile')
    status = models.CharField(
        max_length=3,
        null=False,
        choices=PROFILE_STATUS_CHOICES
    )
