"""
Tests for exam signals
"""
from unittest.mock import patch

from django.test import TestCase

from exams.factories import ExamProfileFactory
from exams.models import ExamProfile
from profiles.factories import ProfileFactory


class ExamSignalsTest(TestCase):
    """
    Tests for exam signals
    """

    @patch('exams.signals.update_exam_profile')
    def test_update_exam_profile_called(self, mock):  # pylint: disable=no-self-use
        """
        Verify that update_exam_profile is called when a profile saves
        """
        profile = ProfileFactory.create()
        profile_exam = ExamProfileFactory.create(profile=profile, status=ExamProfile.PROFILE_SUCCESS)
        profile.first_name = 'NewName'
        profile.save()

        profile_exam.refresh_from_db()

        assert mock.call_count == 1
        assert profile_exam.status == ExamProfile.PROFILE_PENDING
