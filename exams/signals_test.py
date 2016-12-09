"""
Tests for exam signals
"""
from django.contrib.auth.models import User
from django.test import TestCase

from exams.models import ExamProfile


class ExamSignalsTest(TestCase):
    """
    Tests for exam signals
    """

    def test_update_exam_profile_called(self):  # pylint: disable=no-self-use
        """
        Verify that update_exam_profile is called when a profile saves
        """

        user = User.objects.create(username='test')
        profile = user.profile
        profile_exam = ExamProfile.objects.create(
            profile=profile,
            status=ExamProfile.PROFILE_SUCCESS,
        )
        profile.first_name = 'NewName'
        profile.save()

        profile_exam.refresh_from_db()

        assert profile_exam.status == ExamProfile.PROFILE_PENDING
