"""
Tests for exam tasks
"""
from unittest.mock import patch

from django.db.models.signals import post_save
from django.test import (
    override_settings,
    TestCase
)
from factory.django import mute_signals

from exams.factories import ExamProfileFactory
from exams.models import ExamProfile


class ExamSignalsTest(TestCase):
    """
    Tests for exam tasks
    """

    @patch('exams.pearson.upload_tsv')
    @patch('exams.pearson.write_profiles_ccd')
    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_export_exam_profiles(
            self,
            write_profiles_ccd_mock,
            upload_tsv_mock,
    ):  # pylint: disable=no-self-use
        """
        Verify that update_exam_profile is called when a profile saves
        """
        from exams.tasks import export_exam_profiles

        with mute_signals(post_save):
            exam_profiles = ExamProfileFactory.create_batch(5, status=ExamProfile.PROFILE_PENDING)

        export_exam_profiles()

        exam_profile_ids = [exam_profile.id for exam_profile in exam_profiles]
        exam_profiles = ExamProfile.objects.filter(id__in=exam_profile_ids)

        assert upload_tsv_mock.call_count == 1
        assert write_profiles_ccd_mock.call_count == 1

        for exam_profile in exam_profiles:
            assert exam_profile.status == ExamProfile.PROFILE_IN_PROGRESS
