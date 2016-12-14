"""
Models for exams
"""
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Model

from micromasters.models import TimestampedModel


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
        (PROFILE_SUCCESS, 'Sync Succeeded'),
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


class ExamAuthorization(TimestampedModel):
    """
    Tracks state of an exam authorization
    """
    OPERATION_ADD = 'add'
    OPERATION_DELETE = 'delete'
    OPERATION_UPDATE = 'update'

    OPERATION_CHOICES = (
        (OPERATION_ADD, 'Add'),
        (OPERATION_DELETE, 'Update'),
        (OPERATION_UPDATE, 'Delete'),
    )

    STATUS_PENDING = 'pending'
    STATUS_IN_PROGRESS = 'in-progress'
    STATUS_FAILED = 'failed'
    STATUS_SUCCESS = 'success'

    STATUS_CHOICES = (
        (STATUS_PENDING, 'Sync Pending'),
        (STATUS_IN_PROGRESS, 'Sync in Progress'),
        (STATUS_FAILED, 'Sync Failed'),
        (STATUS_SUCCESS, 'Sync Suceeded'),
    )

    user = models.ForeignKey(
        User,
        related_name='exam_authorizations'
    )

    course = models.ForeignKey(
        'courses.Course',
        related_name='exam_authorizations'
    )

    operation = models.CharField(
        max_length=30,
        null=False,
        choices=OPERATION_CHOICES
    )
    status = models.CharField(
        max_length=30,
        null=False,
        choices=STATUS_CHOICES
    )

    date_first_eligible = models.DateTimeField()
    date_last_eligible = models.DateTimeField()

    def __str__(self):
        return 'Exam Authorization "{0}" with status "{1}" for user {2}'.format(
            self.id,
            self.status,
            self.user_id
        )
