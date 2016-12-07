"""
Tests for exam tasks
"""
from unittest.mock import patch

from django.test import (
    override_settings,
    TestCase
)

from exams.factories import ExamProfileFactory
from exams.models import ExamProfile
from exams.tasks import export_exam_profiles


class ExamSignalsTest(TestCase):
    """
    Tests for exam tasks
    """

    @patch('exams.pearson.upload_tsv')
    @patch('exams.pearson.write_profiles_ccd')
    @patch('exams.pearson.profile_to_ccd_row')
    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_export_exam_profiles(
            self,
            upload_tsv_mock,
            write_profiles_ccd_mock,
            profile_to_ccd_row_mock
    ):  # pylint: disable=no-self-use
        """
        Verify that update_exam_profile is called when a profile saves
        """
        exam_profiles = ExamProfileFactory.create_batch(5, status=ExamProfile.PROFILE_PENDING)

        export_exam_profiles()

        exam_profiles.refresh_from_db()

        assert upload_tsv_mock.call_count == 1
        assert write_profiles_ccd_mock.call_count == 1
        assert profile_to_ccd_row_mock.call_count == 5

        for exam_profile in exam_profiles:
            assert exam_profile.status == ExamProfile.PROFILE_IN_PROGRESS
