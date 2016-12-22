"""
Tests for exam tasks
"""
from unittest.mock import patch

from django.db.models.query import QuerySet
from django.db.models.signals import post_save
from django.test import TestCase
from factory.django import mute_signals

from exams.factories import ExamProfileFactory
from exams.models import ExamProfile


class ExamSignalsTest(TestCase):
    """
    Tests for exam tasks
    """

    @patch('exams.pearson.upload_tsv')
    @patch('exams.pearson.write_cdd_file')
    def test_export_exam_profiles(
            self,
            cdd_writer_mock,
            upload_tsv_mock,
    ):  # pylint: disable=no-self-use
        """
        Verify that update_exam_profile is called when a profile saves
        """
        from exams.tasks import export_exam_profiles

        with mute_signals(post_save):
            exam_profiles = ExamProfileFactory.create_batch(10, status=ExamProfile.PROFILE_PENDING)

        valid, invalid = exam_profiles[:5], exam_profiles[5:]

        cdd_writer_mock.return_value = (valid, invalid)

        export_exam_profiles()

        assert upload_tsv_mock.call_count == 1
        assert 'cdd-' in upload_tsv_mock.call_args[0][0]
        assert upload_tsv_mock.call_args[0][0].endswith('.dat')

        assert cdd_writer_mock.call_count == 1
        assert hasattr(cdd_writer_mock.call_args[0][0], 'write')  # was first arg a file-like object?
        assert isinstance(cdd_writer_mock.call_args[0][1], QuerySet)
        assert all([isinstance(ep, ExamProfile) for ep in cdd_writer_mock.args[0][1]])

        for exam_profile in exam_profiles:
            exam_profile.refresh_from_db()

        for exam_profile in invalid:
            assert exam_profile.status == ExamProfile.PROFILE_INVALID

        for exam_profile in valid:
            assert exam_profile.status == ExamProfile.PROFILE_IN_PROGRESS
