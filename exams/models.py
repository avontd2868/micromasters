"""
Models for exams
"""
from django.db import models
from django.db.models import Model


class ExamProfile(Model):
    """
    Profile model to track syncing this data to the remote
    """
    PROFILE_INVALID = 'invalid'
    PROFILE_PENDING = 'pending'
    PROFILE_IN_PROGRESS = 'in-progress'
    PROFILE_FAILED = 'failed'
    PROFILE_SUCCESS = 'success'

    PROFILE_STATUS_CHOICES = (
        (PROFILE_PENDING, 'Sync Pending'),
        (PROFILE_IN_PROGRESS, 'Sync in Progress'),
        (PROFILE_FAILED, 'Sync Failed'),
        (PROFILE_SUCCESS, 'Sync Suceeded'),
        (PROFILE_INVALID, 'Profile Invalid'),
    )

    profile = models.OneToOneField(
        'profiles.Profile',
        related_name='exam_profile'
    )
    status = models.CharField(
        max_length=30,
        null=False,
        choices=PROFILE_STATUS_CHOICES
    )

    def __str__(self):
        return 'Exam Profile "{0}" with status "{1}"'.format(self.id, self.status)
